"""
database/executor.py
Safely executes validated SELECT/WITH queries and returns results as a
pandas DataFrame together with timing information.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

import pandas as pd


@dataclass
class QueryResult:
    """Container for the outcome of a query execution."""

    dataframe: pd.DataFrame
    elapsed: float          # seconds
    row_count: int
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class QueryExecutor:
    """Run read-only queries against a SQLite database file."""

    def __init__(self, db_path: str, row_limit: int = 5000):
        self.db_path = db_path
        self.row_limit = row_limit

    def run(self, sql: str) -> QueryResult:
        """Execute a query and return a QueryResult.

        Any database error is captured and returned in the result rather than
        raised, so the UI can always render a friendly message.
        """
        start = time.perf_counter()
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                df = pd.read_sql_query(sql, conn)
            finally:
                conn.close()

            # Guard against very large result sets in the UI.
            if len(df) > self.row_limit:
                df = df.head(self.row_limit)

            elapsed = time.perf_counter() - start
            return QueryResult(df, elapsed, len(df))
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            elapsed = time.perf_counter() - start
            return QueryResult(pd.DataFrame(), elapsed, 0, error=str(exc))
