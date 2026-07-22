from __future__ import annotations

from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.persistence.elo import compute_new_ratings
from server.persistence.game_repository import GameRepository
from server.persistence.user_repository import UserRepository
from server.protocol.events import GameOverEvent
from server.session.session_registry import SessionRegistry
from server.transport.outbound_message import OutboundMessage


class GameResultRecorder:
    """Subscribes to OUTBOUND, records finished games. Needs both
    `session/` (to look up which players were in a finished session) and
    `persistence/` (to record the result) — the same shape
    `logging_/activity_logger.py` already has, so it sits outside the
    named server-layers, free to depend on both.

    Safe timing: `GameOverEvent` is edge-triggered exactly once per
    session, fired from inside `advance()` before that session becomes
    eligible for reaping (`session_ttl_after_game_over_ms` only starts
    counting down after `GameOverEvent` already went out). So
    `SessionRegistry.get(...)` is guaranteed to still find the session at
    the moment this handler runs — the `if session is None: return` guard
    is defensive, not load-bearing.
    """

    def __init__(
        self,
        bus: EventBus,
        registry: SessionRegistry,
        users: UserRepository,
        games: GameRepository,
        k_factor: int = 32,
    ) -> None:
        self._registry = registry
        self._users = users
        self._games = games
        self._k_factor = k_factor
        bus.subscribe(OUTBOUND, self.handle_outbound)

    def handle_outbound(self, message: OutboundMessage) -> None:
        if not isinstance(message.event, GameOverEvent) or message.session_id is None:
            return
        session = self._registry.get(message.session_id)
        if session is None:
            return

        players = [session.player_for(cid) for cid in session.player_ids]
        white = next(p for p in players if p.color == Color.WHITE)
        black = next(p for p in players if p.color == Color.BLACK)
        white_account = self._users.get(white.username)
        black_account = self._users.get(black.username)

        white_after, black_after = compute_new_ratings(
            white_rating=white_account.elo_rating,
            black_rating=black_account.elo_rating,
            winner_color=message.event.winner,
            k_factor=self._k_factor,
        )

        self._games.record_game(
            session_id=message.session_id,
            white_username=white.username,
            black_username=black.username,
            winner_color=message.event.winner,
            white_rating_before=white_account.elo_rating,
            black_rating_before=black_account.elo_rating,
            white_rating_after=white_after,
            black_rating_after=black_after,
        )
        self._users.update_rating(white.username, white_after)
        self._users.update_rating(black.username, black_after)
