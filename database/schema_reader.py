"""
database/schema_reader.py
Introspects a SQLite database to build a structured schema description
containing tables, columns, primary keys and foreign-key relationships.
"""

from __future__ import annotations

import sqlite3
from typing import Any


class SchemaReader:
    """Read table/column/key metadata from a SQLite connection."""

    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def table_names(self) -> list[str]:
        """Return user tables, excluding SQLite internal tables."""
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cur.fetchall()]

    def _columns(self, table: str) -> list[dict[str, Any]]:
        cur = self.conn.execute(f'PRAGMA table_info("{table}")')
        cols = []
        for cid, name, ctype, notnull, default, pk in cur.fetchall():
            cols.append({
                "name": name,
                "type": ctype or "TEXT",
                "not_null": bool(notnull),
                "primary_key": bool(pk),
            })
        return cols

    def _foreign_keys(self, table: str) -> list[dict[str, str]]:
        cur = self.conn.execute(f'PRAGMA foreign_key_list("{table}")')
        fks = []
        for row in cur.fetchall():
            # row: id, seq, table, from, to, on_update, on_delete, match
            fks.append({
                "from": row[3],
                "to_table": row[2],
                "to_column": row[4],
            })
        return fks

    def _row_count(self, table: str) -> int:
        try:
            cur = self.conn.execute(f'SELECT COUNT(*) FROM "{table}"')
            return int(cur.fetchone()[0])
        except sqlite3.Error:
            return 0

    def build(self) -> dict[str, Any]:
        """Return a full schema dict with aggregate statistics."""
        tables: dict[str, Any] = {}
        total_rows = 0
        total_cols = 0
        total_fks = 0

        for name in self.table_names():
            cols = self._columns(name)
            fks = self._foreign_keys(name)
            rows = self._row_count(name)
            total_rows += rows
            total_cols += len(cols)
            total_fks += len(fks)
            tables[name] = {
                "columns": cols,
                "foreign_keys": fks,
                "row_count": rows,
                "primary_keys": [c["name"] for c in cols if c["primary_key"]],
            }

        return {
            "tables": tables,
            "stats": {
                "table_count": len(tables),
                "row_count": total_rows,
                "column_count": total_cols,
                "relationship_count": total_fks,
            },
        }

    def to_prompt_text(self, schema: dict[str, Any] | None = None) -> str:
        """Serialise the schema into a compact string for LLM prompts."""
        schema = schema or self.build()
        lines: list[str] = []
        for tname, tinfo in schema["tables"].items():
            col_parts = []
            for c in tinfo["columns"]:
                tag = " PK" if c["primary_key"] else ""
                col_parts.append(f"{c['name']} {c['type']}{tag}")
            lines.append(f"TABLE {tname} (" + ", ".join(col_parts) + ")")
            for fk in tinfo["foreign_keys"]:
                lines.append(
                    f"  FK {tname}.{fk['from']} -> "
                    f"{fk['to_table']}.{fk['to_column']}"
                )
        return "\n".join(lines)
