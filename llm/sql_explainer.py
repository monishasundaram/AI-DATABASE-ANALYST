"""
llm/sql_explainer.py
Produce concise, plain-English explanations of SQL queries. Uses the
configured provider when available, otherwise a lightweight rule-based
explainer that inspects clauses of the query.
"""

from __future__ import annotations

import re

from llm.prompts import build_explanation_prompt


class SQLExplainer:
    """Explain a SQL query in <= 80 words using bullet points."""

    def __init__(self, config):
        self.config = config

    def explain(self, sql: str) -> str:
        if self.config.configured:
            try:
                if self.config.provider == "openai":
                    return self._openai(sql)
                return self._gemini(sql)
            except Exception:  # noqa: BLE001 - fall back silently
                return self._offline(sql)
        return self._offline(sql)

    # ------------------------------------------------------------------ #
    def _openai(self, sql: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.config.openai_key)
        resp = client.chat.completions.create(
            model=self.config.openai_model,
            messages=[{"role": "user", "content": build_explanation_prompt(sql)}],
            temperature=0,
        )
        return resp.choices[0].message.content.strip()

    def _gemini(self, sql: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self.config.gemini_key)
        model = genai.GenerativeModel(self.config.gemini_model)
        return model.generate_content(build_explanation_prompt(sql)).text.strip()

    # ------------------------------------------------------------------ #
    def _offline(self, sql: str) -> str:
        """Derive a bullet explanation from the query's clauses."""
        upper = sql.upper()
        bullets: list[str] = []

        tables = re.findall(r"FROM\s+\"?(\w+)\"?", sql, flags=re.IGNORECASE)
        joins = re.findall(r"JOIN\s+\"?(\w+)\"?", sql, flags=re.IGNORECASE)
        all_tables = tables + joins
        if all_tables:
            bullets.append(f"- Reads data from: {', '.join(dict.fromkeys(all_tables))}.")

        if re.search(r"COUNT\(|SUM\(|AVG\(|MIN\(|MAX\(", upper):
            bullets.append("- Aggregates values (count/sum/average) across rows.")
        if "GROUP BY" in upper:
            bullets.append("- Groups results before aggregating.")
        if "WHERE" in upper:
            bullets.append("- Filters rows to those matching the conditions.")
        if "ORDER BY" in upper:
            direction = "descending" if "DESC" in upper else "ascending"
            bullets.append(f"- Sorts the results in {direction} order.")
        m = re.search(r"LIMIT\s+(\d+)", upper)
        if m:
            bullets.append(f"- Returns at most {m.group(1)} rows.")

        if not bullets:
            bullets.append("- Selects rows from the database as written.")
        return "\n".join(bullets)
