from __future__ import annotations

import sqlite3

from kungfu_chess.model import Color


class SqliteGameRepository:
    """Takes an already-open `sqlite3.Connection` — doesn't open its own,
    same rule as `SqliteUserRepository`. `record_game`'s `session_id`
    `UNIQUE` constraint (schema.sql) rejects a duplicate insert with
    `sqlite3.IntegrityError` — defense in depth against a session's result
    ever being recorded twice.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def record_game(
        self,
        session_id: str,
        white_username: str,
        black_username: str,
        winner_color: Color,
        white_rating_before: int,
        black_rating_before: int,
        white_rating_after: int,
        black_rating_after: int,
    ) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO games (
                    session_id, white_username, black_username, winner_color,
                    white_rating_before, black_rating_before,
                    white_rating_after, black_rating_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    white_username,
                    black_username,
                    winner_color.value,
                    white_rating_before,
                    black_rating_before,
                    white_rating_after,
                    black_rating_after,
                ),
            )
