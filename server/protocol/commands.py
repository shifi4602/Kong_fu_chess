from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from kungfu_chess.model import Position


class MatchMode(Enum):
    QUICK_MATCH = "quick_match"
    ROOM = "room"


@dataclass(frozen=True)
class JoinCommand:
    trace_id: str
    username: str
    password: str
    mode: MatchMode = MatchMode.QUICK_MATCH
    room_id: Optional[str] = None


@dataclass(frozen=True)
class MoveCommand:
    trace_id: str
    src: Position
    dst: Position


@dataclass(frozen=True)
class JumpCommand:
    trace_id: str
    position: Position


@dataclass(frozen=True)
class HeartbeatCommand:
    trace_id: str
    client_send_ms: int
