"""
llm/sql_generator.py
Natural-language -> SQL generation with pluggable providers (OpenAI /
Gemini) and a deterministic offline fallback so the application always
returns a usable query, even without an API key configured.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from llm.prompts import SQL_SYSTEM_PROMPT, build_generation_prompt


@dataclass
class GenerationResult:
    """Result of an NL->SQL generation attempt."""

    sql: str
    explanation: str
    safe: bool
    source: str          # "openai" | "gemini" | "offline"
    error: str | None = None


class SQLGenerator:
    """Generate SQL from natural language using the configured provider."""

    def __init__(self, config):
        self.config = config

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate(
        self, question: str, schema_text: str, schema: dict, history: str = ""
    ) -> GenerationResult:
        """Return a GenerationResult for the user's question.

        Falls back to a heuristic generator when no provider is configured
        or when a provider call fails, ensuring the pipeline never dead-ends.
        """
        if self.config.configured:
            try:
                if self.config.provider == "openai":
                    return self._via_openai(question, schema_text)
                return self._via_gemini(question, schema_text)
            except Exception as exc:  # noqa: BLE001 - degrade gracefully
                fallback = self._offline(question, schema)
                fallback.error = f"AI provider error, used offline mode: {exc}"
                return fallback
        return self._offline(question, schema)

    # ------------------------------------------------------------------ #
    # Providers
    # ------------------------------------------------------------------ #
    def _via_openai(self, question: str, schema_text: str) -> GenerationResult:
        from openai import OpenAI

        client = OpenAI(api_key=self.config.openai_key)
        resp = client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": SQL_SYSTEM_PROMPT},
                {"role": "user", "content": build_generation_prompt(schema_text, question)},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        payload = json.loads(resp.choices[0].message.content)
        return GenerationResult(
            sql=payload.get("sql", "").strip(),
            explanation=payload.get("explanation", "").strip(),
            safe=bool(payload.get("safe", True)),
            source="openai",
        )

    def _via_gemini(self, question: str, schema_text: str) -> GenerationResult:
        import google.generativeai as genai

        genai.configure(api_key=self.config.gemini_key)
        model = genai.GenerativeModel(
            self.config.gemini_model, system_instruction=SQL_SYSTEM_PROMPT
        )
        resp = model.generate_content(build_generation_prompt(schema_text, question))
        payload = self._extract_json(resp.text)
        return GenerationResult(
            sql=payload.get("sql", "").strip(),
            explanation=payload.get("explanation", "").strip(),
            safe=bool(payload.get("safe", True)),
            source="gemini",
        )

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Pull the first JSON object out of a model response."""
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model response.")
        return json.loads(match.group(0))

    # ------------------------------------------------------------------ #
    # Offline heuristic generator
    # ------------------------------------------------------------------ #
    def _offline(self, question: str, schema: dict) -> GenerationResult:
        """A best-effort, rule-based generator used without an API key.

        It picks the most relevant table by keyword overlap and builds a
        sensible SELECT, honouring simple intents like "top", "count",
        "average" and "recent".
        """
        q = question.lower()
        tables = schema.get("tables", {})
        if not tables:
            return GenerationResult(
                "SELECT 1;", "No tables available in the schema.", True, "offline"
            )

        # Choose the table whose name best matches the question.
        def score(name: str) -> int:
            singular = name.lower().rstrip("s")
            return sum(kw in q for kw in {name.lower(), singular})

        table = max(tables, key=score)
        if score(table) == 0:
            table = next(iter(tables))  # default to first table

        cols = [c["name"] for c in tables[table]["columns"]]
        numeric = [
            c["name"] for c in tables[table]["columns"]
            if c["type"].upper() in {"REAL", "INTEGER", "NUMERIC", "INT", "FLOAT"}
            and not c["primary_key"]
        ]

        # Intent: destructive / write request. We surface the statement the
        # user is asking for so the safety validator visibly blocks it, rather
        # than silently returning a harmless SELECT.
        destructive = [
            (r"\b(delete|remove)\b", f'DELETE FROM "{table}" WHERE 1=1;'),
            (r"\bdrop\b", f'DROP TABLE "{table}";'),
            (r"\btruncate\b", f'DELETE FROM "{table}";'),
            (r"\b(update|change|modify|set)\b", f'UPDATE "{table}" SET column = value;'),
            (r"\b(insert|create)\b", f'INSERT INTO "{table}" (column) VALUES (value);'),
        ]
        for pattern, stmt in destructive:
            if re.search(pattern, q):
                return GenerationResult(
                    stmt,
                    "- This is a write/destructive operation.\n"
                    "- Only read-only SELECT queries are allowed, so this is blocked.",
                    False,
                    "offline",
                )

        # Intent: count
        if "how many" in q or q.startswith("count") or "number of" in q:
            sql = f'SELECT COUNT(*) AS total FROM "{table}";'
            expl = f"- Counts all rows in the {table} table."
            return GenerationResult(sql, expl, True, "offline")

        # Intent: average / sum on a numeric column
        agg = "AVG" if ("average" in q or "avg" in q) else "SUM" if "total" in q or "sum" in q else None
        if agg and numeric:
            col = numeric[0]
            sql = f'SELECT {agg}("{col}") AS {agg.lower()}_{col} FROM "{table}";'
            expl = f"- Computes the {agg.lower()} of {col} across {table}."
            return GenerationResult(sql, expl, True, "offline")

        # Intent: top / highest -> order by a numeric column desc
        if any(w in q for w in ("top", "highest", "most", "best", "largest")) and numeric:
            col = numeric[-1]
            sql = (
                f'SELECT * FROM "{table}" ORDER BY "{col}" DESC LIMIT 10;'
            )
            expl = f"- Returns the 10 {table} rows with the highest {col}."
            return GenerationResult(sql, expl, True, "offline")

        # Intent: recent / latest -> order by a date column
        date_cols = [c for c in cols if "date" in c.lower()]
        if any(w in q for w in ("recent", "latest", "newest")) and date_cols:
            col = date_cols[0]
            sql = f'SELECT * FROM "{table}" ORDER BY "{col}" DESC LIMIT 10;'
            expl = f"- Returns the 10 most recent {table} rows by {col}."
            return GenerationResult(sql, expl, True, "offline")

        # Default: preview the table.
        sql = f'SELECT * FROM "{table}" LIMIT 20;'
        expl = (
            f"- Previews the first 20 rows of the {table} table.\n"
            "- Offline mode: connect an AI provider in Settings for smarter SQL."
        )
        return GenerationResult(sql, expl, True, "offline")