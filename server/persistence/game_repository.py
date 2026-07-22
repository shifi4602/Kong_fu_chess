from __future__ import annotations

from typing import List, Protocol

from kungfu_chess.model import Color


class DuplicateGameError(Exception):
    """Raised by record_game() when session_id has already been recorded.

    Defense in depth: `GameOverEvent` fires exactly once per session
    (edge-triggered), so this should never actually trigger in practice —
    but if a future change ever causes a duplicate recording attempt, this
    is what stops it from silently double-counting a rating change.
    """


class GameRepository(Protocol):
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
    ) -> None: ...


class InMemoryGameRepository:
    """Zero-I/O double for tests — records every call's arguments in
    `.recorded` so a test can assert on them directly.
    """

    def __init__(self) -> None:
        self._session_ids: set = set()
        self.recorded: List[dict] = []

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
        if session_id in self._session_ids:
            raise DuplicateGameError(session_id)
        self._session_ids.add(session_id)
        self.recorded.append(
            {
                "session_id": session_id,
                "white_username": white_username,
                "black_username": black_username,
                "winner_color": winner_color,
                "white_rating_before": white_rating_before,
                "black_rating_before": black_rating_before,
                "white_rating_after": white_rating_after,
                "black_rating_after": black_rating_after,
            }
        )
