import pytest

from kungfu_chess.model import Color
from server.persistence.game_repository import DuplicateGameError, InMemoryGameRepository


def _record(repo, session_id="s1"):
    repo.record_game(
        session_id=session_id,
        white_username="alice",
        black_username="bob",
        winner_color=Color.WHITE,
        white_rating_before=1200,
        black_rating_before=1200,
        white_rating_after=1216,
        black_rating_after=1184,
    )


def test_record_game_is_captured_verbatim():
    repo = InMemoryGameRepository()
    _record(repo)

    assert len(repo.recorded) == 1
    row = repo.recorded[0]
    assert row["session_id"] == "s1"
    assert row["white_username"] == "alice"
    assert row["black_username"] == "bob"
    assert row["winner_color"] == Color.WHITE
    assert row["white_rating_after"] == 1216
    assert row["black_rating_after"] == 1184


def test_duplicate_session_id_raises():
    repo = InMemoryGameRepository()
    _record(repo, session_id="s1")
    with pytest.raises(DuplicateGameError):
        _record(repo, session_id="s1")
