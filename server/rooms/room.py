from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from server.session.game_session import GameSession
from server.transport.connection import Connection


@dataclass(frozen=True)
class _PendingPlayer:
    connection: Connection
    username: str
    trace_id: str


@dataclass
class Room:
    """Mutable state for one room id (docs/ROOMS_PLAN.md §5). `white`/`black`
    are set the instant each of the first two participants joins; `session`
    is created the moment `black` is set. Everyone after that is a
    spectator — pending (room_id known, but no session yet) or attached
    (added to the live `GameSession` directly).
    """

    room_id: str
    white: Optional[_PendingPlayer] = None
    black: Optional[_PendingPlayer] = None
    session: Optional[GameSession] = None
    pending_spectator_ids: List[str] = field(default_factory=list)
    spectator_ids: Set[str] = field(default_factory=set)
