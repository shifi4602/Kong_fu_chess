import sqlite3

import pytest

from kungfu_chess.model import Color
from server.persistence import db
from server.persistence.sqlite_game_repository import SqliteGameRepository
from server.persistence.sqlite_user_repository import SqliteUserRepository


def _repos():
    conn = db.connect(":memory:")
    users = SqliteUserRepository(conn)
    games = SqliteGameRepository(conn)
    users.create_account("alice", "pw1")
    users.create_account("bob", "pw2")
    return conn, games


def test_record_game_round_trips_every_column():
    conn, games = _repos()
    games.record_game(
        session_id="s1",
        white_username="alice",
        black_username="bob",
        winner_color=Color.WHITE,
        white_rating_before=1200,
        black_rating_before=1200,
        white_rating_after=1216,
        black_rating_after=1184,
    )

    row = conn.execute("SELECT * FROM games WHERE session_id = 's1'").fetchone()
    assert row["white_username"] == "alice"
    assert row["black_username"] == "bob"
    assert row["winner_color"] == "white"
    assert row["white_rating_before"] == 1200
    assert row["black_rating_before"] == 1200
    assert row["white_rating_after"] == 1216
    assert row["black_rating_after"] == 1184
    assert row["recorded_at_utc"]


def test_duplicate_session_id_is_rejected_by_the_unique_constraint():
    conn, games = _repos()
    games.record_game(
        session_id="s1",
        white_username="alice",
        black_username="bob",
        winner_color=Color.WHITE,
        white_rating_before=1200,
        black_rating_before=1200,
        white_rating_after=1216,
        black_rating_after=1184,
    )

    with pytest.raises(sqlite3.IntegrityError):
        games.record_game(
            session_id="s1",
            white_username="alice",
            black_username="bob",
            winner_color=Color.BLACK,
            white_rating_before=1216,
            black_rating_before=1184,
            white_rating_after=1200,
            black_rating_after=1200,
        )
