from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from kungfu_chess.model import Color

from .errors import ErrorCode
from .state_records import JumpRecord, MotionRecord, PieceRecord


@dataclass(frozen=True)
class WelcomeEvent:
    trace_id: str
    connection_id: str
    color: Optional[Color]  # None means "you are a spectator" — see docs/ROOMS_PLAN.md §3


@dataclass(frozen=True)
class PlayerJoinedEvent:
    trace_id: str
    color: Color


@dataclass(frozen=True)
class StateEvent:
    trace_id: str
    pieces: Tuple[PieceRecord, ...]
    motions: Tuple[MotionRecord, ...]
    jumps: Tuple[JumpRecord, ...]
    current_time: float
    winner: Optional[Color]


@dataclass(frozen=True)
class HeartbeatEvent:
    trace_id: str
    connection_id: str
    client_send_ms: int
    server_time_ms: int


@dataclass(frozen=True)
class MoveRejectedEvent:
    trace_id: str
    connection_id: str
    reason: ErrorCode


@dataclass(frozen=True)
class GameOverEvent:
    trace_id: str
    winner: Color


@dataclass(frozen=True)
class ErrorEvent:
    trace_id: str
    connection_id: str
    reason: ErrorCode


@dataclass(frozen=True)
class NoOpEvent:
    """Sentinel return value for a handler with nothing to unicast.

    Not part of the wire protocol (absent from codec.py's type registry) and
    never published on the bus — the resulting StateEvent broadcast on the
    next tick is the real signal, per §7 of docs/SERVER_PLAN.md. Handlers
    return this instead of `None` so the return type stays a total, typed
    `Event`, with no special-cased falsy value for callers to check.
    """
