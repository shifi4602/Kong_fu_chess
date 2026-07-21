from __future__ import annotations

from typing import Dict, List

from server.config import ServerConfig
from server.session.game_session import GameSession


class SessionRegistry:
    """Active `GameSession`s, keyed by session id. `.tick_all(now_ms)` is
    pure and sync — the same `now_ms` read once by the scheduler (§9.1)
    drives every session in one pass. Also reaps finished sessions once
    their grace period has elapsed (§9.6), so this dict doesn't grow
    without bound.
    """

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._sessions: Dict[str, GameSession] = {}
        self._session_id_by_connection: Dict[str, str] = {}

    def add(self, session: GameSession) -> None:
        self._sessions[session.session_id] = session
        for connection_id in session.player_ids:
            self._session_id_by_connection[connection_id] = session.session_id

    def get(self, session_id: str) -> GameSession | None:
        return self._sessions.get(session_id)

    def find_session_for_connection(self, connection_id: str) -> GameSession | None:
        session_id = self._session_id_by_connection.get(connection_id)
        if session_id is None:
            return None
        return self._sessions.get(session_id)

    def __len__(self) -> int:
        return len(self._sessions)

    def __contains__(self, session_id: str) -> bool:
        return session_id in self._sessions

    def tick_all(self, now_ms: int) -> None:
        finished: List[str] = []
        for session_id, session in self._sessions.items():
            session.advance(now_ms)
            if (
                session.is_terminal
                and session.ms_since_finished >= self._config.session_ttl_after_game_over_ms
            ):
                finished.append(session_id)
        for session_id in finished:
            session = self._sessions.pop(session_id)
            for connection_id in session.player_ids:
                self._session_id_by_connection.pop(connection_id, None)
