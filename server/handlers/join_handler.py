from __future__ import annotations

from typing import Optional, Protocol

from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.clock import WallClock
from server.persistence.user_repository import InvalidCredentialsError, UserRepository
from server.protocol.commands import JoinCommand, MatchMode
from server.protocol.errors import ErrorCode
from server.protocol.events import ErrorEvent, PlayerJoinedEvent, WelcomeEvent
from server.session.session_registry import SessionRegistry
from server.transport.connection import Connection
from server.transport.outbound_message import OutboundMessage


class _JoinLobby(Protocol):
    """Structural interface for whatever pairs joiners into a game.
    `matchmaking.Lobby` satisfies this without `handlers/` importing
    `matchmaking/` directly — `server.handlers` and `server.matchmaking`
    are sibling layers in `.importlinter`'s `server-layers` contract
    (neither may depend on the other); `server/main.py`, the composition
    root, is the only place a concrete `Lobby` gets wired in (§11).
    """

    def join(self, connection: Connection, username: str, trace_id: str, now_ms: int) -> Optional[object]:
        ...


class _RoomJoiner(Protocol):
    """Same structural seam as `_JoinLobby`, for `rooms.RoomRegistry` —
    `server.rooms` is also a sibling of `server.handlers`
    (docs/ROOMS_PLAN.md §14). The returned object is consumed by plain
    attribute access in `_handle_room_join` below, never `isinstance`.
    """

    def join(
        self, connection: Connection, username: str, trace_id: str, room_id: str, now_ms: int
    ) -> object:
        ...


class JoinHandler:
    def __init__(
        self,
        lobby: _JoinLobby,
        users: UserRepository,
        bus: EventBus,
        wall_clock: WallClock,
        registry: SessionRegistry,
        rooms: _RoomJoiner,
    ) -> None:
        self._lobby = lobby
        self._users = users
        self._bus = bus
        self._wall_clock = wall_clock
        self._registry = registry
        self._rooms = rooms

    def handle(self, connection: Connection, cmd: JoinCommand) -> None:
        try:
            if self._users.get(cmd.username) is None:
                account = self._users.create_account(cmd.username, cmd.password)
            else:
                account = self._users.authenticate(cmd.username, cmd.password)
        except InvalidCredentialsError:
            self._bus.publish(
                OUTBOUND,
                OutboundMessage.unicast(
                    ErrorEvent(
                        trace_id=cmd.trace_id,
                        connection_id=connection.id,
                        reason=ErrorCode.INVALID_CREDENTIALS,
                    ),
                    connection.id,
                ),
            )
            return

        now_ms = self._wall_clock.now_ms()

        # "If he comes back, the game continues like it was" — a username
        # with an in-progress GameSession reconnects to it instead of
        # entering matchmaking again (docs/SERVER_PLAN.md §16's
        # deliberately-deferred "reconnect identity", closed here).
        reconnected = self._registry.reconnect(cmd.username, connection, now_ms)
        if reconnected is not None:
            _, player = reconnected
            self._bus.publish(
                OUTBOUND,
                OutboundMessage.unicast(
                    WelcomeEvent(trace_id=cmd.trace_id, connection_id=player.id, color=player.color),
                    player.id,
                ),
            )
            return

        if cmd.mode is MatchMode.ROOM:
            self._handle_room_join(connection, cmd, now_ms)
            return

        result = self._lobby.join(connection, cmd.username, cmd.trace_id, now_ms, account.elo_rating)
        if result is None:
            # First joiner: waits silently. Stage 1's closed event set
            # (§5) has no "waiting" acknowledgment — WelcomeEvent is only
            # meaningful once a color's been assigned, which happens at
            # pairing.
            return

        self._bus.publish(
            OUTBOUND,
            OutboundMessage.unicast(
                WelcomeEvent(trace_id=result.white_trace_id, connection_id=result.white.id, color=Color.WHITE),
                result.white.id,
            ),
        )
        self._bus.publish(
            OUTBOUND,
            OutboundMessage.unicast(
                WelcomeEvent(trace_id=result.black_trace_id, connection_id=result.black.id, color=Color.BLACK),
                result.black.id,
            ),
        )
        self._bus.publish(
            OUTBOUND,
            OutboundMessage.broadcast(
                PlayerJoinedEvent(trace_id=result.black_trace_id, color=Color.BLACK),
                (result.white.id, result.black.id),
            ),
        )

    def _handle_room_join(self, connection: Connection, cmd: JoinCommand, now_ms: int) -> None:
        outcome = self._rooms.join(connection, cmd.username, cmd.trace_id, cmd.room_id or "", now_ms)

        if outcome.error is not None:
            self._unicast(ErrorEvent(trace_id=cmd.trace_id, connection_id=connection.id, reason=outcome.error), connection.id)
            return

        if outcome.game_started:
            self._unicast(
                WelcomeEvent(trace_id=outcome.white_trace_id, connection_id=outcome.white.id, color=Color.WHITE),
                outcome.white.id,
            )
            self._unicast(
                WelcomeEvent(trace_id=outcome.black_trace_id, connection_id=outcome.black.id, color=Color.BLACK),
                outcome.black.id,
            )
            for spectator_id in outcome.attached_spectator_ids:
                self._unicast(
                    WelcomeEvent(trace_id=cmd.trace_id, connection_id=spectator_id, color=None), spectator_id
                )
            recipients = (outcome.white.id, outcome.black.id, *outcome.attached_spectator_ids)
            self._broadcast(PlayerJoinedEvent(trace_id=outcome.black_trace_id, color=Color.BLACK), recipients)
            return

        # Seated as the room's first player (color=WHITE) or as a
        # spectator (color=None) — both get an immediate ack, deliberately
        # unlike quick-match's silent first joiner (docs/ROOMS_PLAN.md §11).
        self._unicast(WelcomeEvent(trace_id=cmd.trace_id, connection_id=connection.id, color=outcome.color), connection.id)

    def _unicast(self, event: object, connection_id: str) -> None:
        self._bus.publish(OUTBOUND, OutboundMessage.unicast(event, connection_id))

    def _broadcast(self, event: object, connection_ids) -> None:
        self._bus.publish(OUTBOUND, OutboundMessage.broadcast(event, connection_ids))
