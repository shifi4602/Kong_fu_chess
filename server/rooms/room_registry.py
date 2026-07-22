from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from kungfu_chess.model import Color

from server.config import ServerConfig
from server.protocol.errors import ErrorCode
from server.rooms.room import Room, _PendingPlayer
from server.session.player_session import PlayerSession
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import Connection

_ROOM_ID_CHARSET = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class RoomJoinOutcome:
    """A closed, flat result for `RoomRegistry.join()` — deliberately not a
    discriminated union of separate dataclasses: `server.handlers` and
    `server.rooms` are sibling layers in `.importlinter`'s
    `server-layers` contract, so `JoinHandler` must consume this by plain
    attribute access (duck typing), never `isinstance`, mirroring how it
    already consumes `matchmaking.lobby.Lobby`'s `PairingResult` through
    the `_JoinLobby` Protocol. Exactly one shape is meaningful per
    outcome:

    - rejected: `error` set, nothing else meaningful.
    - seated as the room's first player: `color=WHITE`, everything else default.
    - seated as a spectator: `color=None`, everything else default.
    - the game just started (this join was the 2nd player): `color=BLACK`,
      `game_started=True`, `white`/`black`/`white_trace_id`/`black_trace_id`/
      `attached_spectator_ids` all set.
    """

    error: Optional[ErrorCode] = None
    color: Optional[Color] = None
    game_started: bool = False
    white: Optional[PlayerSession] = None
    black: Optional[PlayerSession] = None
    white_trace_id: Optional[str] = None
    black_trace_id: Optional[str] = None
    attached_spectator_ids: Tuple[str, ...] = ()


class RoomRegistry:
    """Pairs joiners into `GameSession`s by an explicit, client-chosen
    room id instead of `matchmaking.lobby.Lobby`'s anonymous
    first-come/ELO-window pool. The first two participants for a given
    room id are seated as White/Black; every participant after that is a
    read-only spectator, attached to the room's `GameSession` once one
    exists (docs/ROOMS_PLAN.md §5).
    """

    def __init__(
        self, factory: GameSessionFactory, registry: SessionRegistry, config: ServerConfig
    ) -> None:
        self._factory = factory
        self._registry = registry
        self._config = config
        self._rooms: Dict[str, Room] = {}

    def join(
        self, connection: Connection, username: str, trace_id: str, room_id: str, now_ms: int
    ) -> RoomJoinOutcome:
        if (
            not room_id
            or len(room_id) > self._config.room_id_max_length
            or not _ROOM_ID_CHARSET.match(room_id)
        ):
            return RoomJoinOutcome(error=ErrorCode.INVALID_ROOM_ID)

        room = self._rooms.setdefault(room_id, Room(room_id=room_id))

        if room.white is None:
            room.white = _PendingPlayer(connection=connection, username=username, trace_id=trace_id)
            return RoomJoinOutcome(color=Color.WHITE)

        if room.black is None:
            room.black = _PendingPlayer(connection=connection, username=username, trace_id=trace_id)
            session, players = self._factory.create(
                white_connection=room.white.connection,
                white_username=room.white.username,
                black_connection=connection,
                black_username=username,
                now_ms=now_ms,
            )
            self._registry.add(session)

            attached = tuple(room.pending_spectator_ids)
            for spectator_id in attached:
                session.add_spectator(spectator_id)
                self._registry.add_spectator(session.session_id, spectator_id)

            room.session = session
            room.pending_spectator_ids = []

            white_player = players[room.white.connection.id]
            black_player = players[connection.id]
            return RoomJoinOutcome(
                color=Color.BLACK,
                game_started=True,
                white=white_player,
                black=black_player,
                white_trace_id=room.white.trace_id,
                black_trace_id=trace_id,
                attached_spectator_ids=attached,
            )

        total_spectators = len(room.spectator_ids) + len(room.pending_spectator_ids)
        if total_spectators >= self._config.max_spectators_per_room:
            return RoomJoinOutcome(error=ErrorCode.ROOM_FULL)

        if room.session is not None:
            room.session.add_spectator(connection.id)
            self._registry.add_spectator(room.session.session_id, connection.id)
            room.spectator_ids.add(connection.id)
        else:
            room.pending_spectator_ids.append(connection.id)

        return RoomJoinOutcome(color=None)

    def remove_participant(self, connection_id: str) -> None:
        """Disconnect cleanup for a participant who never made it into a
        `GameSession` — a solo pending White, or a pending spectator
        waiting on a 2nd player. Once a room has a `GameSession`,
        disconnect handling is that session's job (docs/ROOMS_PLAN.md §7),
        not this method's.
        """
        for room in self._rooms.values():
            if room.session is not None:
                continue
            if room.white is not None and room.white.connection.id == connection_id:
                room.white = None
            room.pending_spectator_ids = [
                c for c in room.pending_spectator_ids if c != connection_id
            ]

    def tick(self, now_ms: int) -> None:
        """Drops rooms whose `GameSession` has already been reaped from
        `SessionRegistry` (docs/SERVER_PLAN.md §9.6) — the room id becomes
        reusable for a brand new game (docs/ROOMS_PLAN.md §9).
        """
        finished_ids = [
            room_id
            for room_id, room in self._rooms.items()
            if room.session is not None and room.session.session_id not in self._registry
        ]
        for room_id in finished_ids:
            del self._rooms[room_id]
