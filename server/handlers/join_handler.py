from __future__ import annotations

from typing import Optional, Protocol

from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.clock import WallClock
from server.persistence.user_repository import UserRepository
from server.protocol.commands import JoinCommand
from server.protocol.events import PlayerJoinedEvent, WelcomeEvent
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


class JoinHandler:
    def __init__(self, lobby: _JoinLobby, users: UserRepository, bus: EventBus, wall_clock: WallClock) -> None:
        self._lobby = lobby
        self._users = users
        self._bus = bus
        self._wall_clock = wall_clock

    def handle(self, connection: Connection, cmd: JoinCommand) -> None:
        self._users.register(cmd.username)

        result = self._lobby.join(connection, cmd.username, cmd.trace_id, self._wall_clock.now_ms())
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
