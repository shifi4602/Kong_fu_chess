from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from server.matchmaking.strategy import MatchmakingStrategy, Waiter
from server.session.game_session import GameSession
from server.session.player_session import PlayerSession
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import Connection


@dataclass(frozen=True)
class PairingResult:
    session: GameSession
    white: PlayerSession
    black: PlayerSession
    white_trace_id: str
    black_trace_id: str


class Lobby:
    """Pairs waiting joiners into `GameSession`s via a pluggable
    `MatchmakingStrategy` (§6). `Lobby` only ever creates a `GameSession`
    once two joiners are paired — there's nothing to leak in
    `SessionRegistry` before that point (§9.6).
    """

    def __init__(
        self, strategy: MatchmakingStrategy, factory: GameSessionFactory, registry: SessionRegistry
    ) -> None:
        self._strategy = strategy
        self._factory = factory
        self._registry = registry
        self._waiting: List[Waiter] = []

    def join(
        self, connection: Connection, username: str, trace_id: str, now_ms: int
    ) -> Optional[PairingResult]:
        self._waiting.append(Waiter(connection=connection, username=username, trace_id=trace_id))

        match = self._strategy.try_match(self._waiting)
        if match is None:
            return None

        first, second = match
        self._waiting.remove(first)
        self._waiting.remove(second)

        session, players = self._factory.create(
            white_connection=first.connection,
            white_username=first.username,
            black_connection=second.connection,
            black_username=second.username,
            now_ms=now_ms,
        )
        self._registry.add(session)

        return PairingResult(
            session=session,
            white=players[first.connection.id],
            black=players[second.connection.id],
            white_trace_id=first.trace_id,
            black_trace_id=second.trace_id,
        )
