"""
llm/optimizer.py
Static analysis of a SQL query that produces concrete optimisation
suggestions and an estimated performance-improvement percentage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class OptimizationReport:
    """Suggestions and an estimated improvement percentage."""

    suggestions: list[str] = field(default_factory=list)
    estimated_gain: int = 0        # percentage 0-100

    @property
    def has_suggestions(self) -> bool:
        return bool(self.suggestions)


class SQLOptimizer:
    """Rule-based optimiser that inspects a query for common issues."""

    def analyze(self, sql: str, schema: dict | None = None) -> OptimizationReport:
        upper = sql.upper()
        suggestions: list[str] = []
        gain = 0

        # 1. SELECT * -> project explicit columns.
        if re.search(r"SELECT\s+\*", upper):
            suggestions.append(
                "Replace SELECT * with the specific columns you need to reduce "
                "I/O and network transfer."
            )
            gain += 20

        # 2. Missing WHERE on a full scan.
        if "WHERE" not in upper and "GROUP BY" not in upper and "LIMIT" not in upper:
            suggestions.append(
                "Add a WHERE filter or LIMIT to avoid scanning the entire table."
            )
            gain += 15

        # 3. Indexing recommendations from WHERE / JOIN / ORDER BY columns.
        index_cols = set()
        for pattern in (r"WHERE\s+\"?(\w+)\"?", r"ON\s+\"?\w+\"?\.?\"?(\w+)\"?",
                        r"ORDER BY\s+\"?(\w+)\"?"):
            index_cols.update(re.findall(pattern, upper))
        if index_cols:
            cols = ", ".join(sorted(c.lower() for c in index_cols))
            suggestions.append(
                f"Consider indexes on frequently filtered/sorted columns: {cols}."
            )
            gain += 10

        # 4. Many joins.
        join_count = upper.count("JOIN")
        if join_count >= 3:
            suggestions.append(
                f"Query has {join_count} joins — verify each is necessary; "
                "unnecessary joins multiply work."
            )
            gain += 10

        # 5. DISTINCT often masks a join fan-out.
        if "DISTINCT" in upper and join_count:
            suggestions.append(
                "DISTINCT combined with joins can hide duplicate fan-out; "
                "check join keys instead."
            )
            gain += 5

        # 6. Functions on columns in WHERE prevent index use.
        if re.search(r"WHERE[^;]*\b(LOWER|UPPER|SUBSTR|DATE)\s*\(", upper):
            suggestions.append(
                "Avoid wrapping filtered columns in functions; it prevents index use."
            )
            gain += 8

        if not suggestions:
            suggestions.append("Query looks efficient — no obvious improvements found.")

        return OptimizationReport(suggestions=suggestions, estimated_gain=min(gain, 85))
