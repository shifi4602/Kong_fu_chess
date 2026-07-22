from __future__ import annotations

from dataclasses import dataclass

from kungfu_chess.model import Position


@dataclass(frozen=True)
class JoinCommand:
    trace_id: str
    username: str
    password: str


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
