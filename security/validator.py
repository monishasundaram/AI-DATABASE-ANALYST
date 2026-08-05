"""
security/validator.py
Strict, allow-list based SQL validator. Only read-only SELECT / WITH
statements are permitted. Everything else is rejected before execution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Statements that must never run against the user's database.
FORBIDDEN = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "PRAGMA", "ATTACH", "DETACH", "VACUUM", "REPLACE",
    "REINDEX", "ANALYZE", "GRANT", "REVOKE",
}


@dataclass
class ValidationResult:
    """Outcome of validating a SQL string."""

    safe: bool
    reason: str = ""
    normalized: str = ""


class SQLValidator:
    """Validate that a SQL string is a single read-only query."""

    def _strip(self, sql: str) -> str:
        """Remove comments and collapse whitespace for reliable checks."""
        # Remove block comments.
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        # Remove line comments.
        sql = re.sub(r"--[^\n]*", " ", sql)
        return sql.strip().rstrip(";").strip()

    def validate(self, sql: str) -> ValidationResult:
        """Return a ValidationResult describing whether ``sql`` is safe."""
        if not sql or not sql.strip():
            return ValidationResult(False, "Empty query.")

        cleaned = self._strip(sql)
        upper = cleaned.upper()

        # Reject multiple statements (stacked queries).
        if ";" in cleaned:
            return ValidationResult(
                False, "Multiple statements are not allowed.", cleaned
            )

        # Must start with SELECT or WITH.
        if not (upper.startswith("SELECT") or upper.startswith("WITH")):
            return ValidationResult(
                False, "Only SELECT or WITH (read-only) queries are allowed.", cleaned
            )

        # Reject any forbidden keyword appearing as a whole word.
        for kw in FORBIDDEN:
            if re.search(rf"\b{kw}\b", upper):
                return ValidationResult(
                    False, f"Disallowed keyword detected: {kw}.", cleaned
                )

        return ValidationResult(True, "Query is read-only and safe.", cleaned)
