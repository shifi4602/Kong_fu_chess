from __future__ import annotations

import sqlite3
from importlib import resources


def connect(path: str) -> sqlite3.Connection:
    """Open a connection and apply the schema idempotently. `path` can be
    a real file path or ":memory:" — the latter is exactly how tests get a
    fresh, isolated database per test; it needs no test-only code path
    here since it's an entirely ordinary argument to `sqlite3.connect`.
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    apply_schema(conn)
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    schema_sql = resources.files("server.persistence").joinpath("schema.sql").read_text()
    with conn:
        conn.executescript(schema_sql)
