"""
history/storage.py
Persistent query-history store backed by a local SQLite database.
Supports save, list, search, delete, bookmark and reuse.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime

HISTORY_DB = os.path.join(os.path.dirname(__file__), "history.db")


@dataclass
class HistoryItem:
    """A single stored query record."""

    id: int
    question: str
    sql: str
    timestamp: str
    exec_ms: float
    rows: int
    bookmarked: int


class HistoryManager:
    """CRUD interface over the persistent history database."""

    def __init__(self, db_path: str = HISTORY_DB):
        self.db_path = db_path
        self._ensure_table()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    question   TEXT NOT NULL,
                    sql        TEXT NOT NULL,
                    timestamp  TEXT NOT NULL,
                    exec_ms    REAL NOT NULL,
                    rows       INTEGER NOT NULL,
                    bookmarked INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    # ------------------------------------------------------------------ #
    def add(self, question: str, sql: str, exec_ms: float, rows: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO history (question, sql, timestamp, exec_ms, rows) "
                "VALUES (?,?,?,?,?)",
                (question, sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 round(exec_ms, 1), rows),
            )

    def all(self, search: str = "", bookmarked_only: bool = False) -> list[HistoryItem]:
        query = "SELECT * FROM history"
        clauses, params = [], []
        if search:
            clauses.append("(question LIKE ? OR sql LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]
        if bookmarked_only:
            clauses.append("bookmarked = 1")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [HistoryItem(**dict(r)) for r in rows]

    def recent(self, limit: int = 5) -> list[HistoryItem]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [HistoryItem(**dict(r)) for r in rows]

    def delete(self, item_id: int) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (item_id,))

    def toggle_bookmark(self, item_id: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE history SET bookmarked = 1 - bookmarked WHERE id = ?",
                (item_id,),
            )

    def clear(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM history")

    def count(self) -> int:
        with self._conn() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM history").fetchone()[0])
