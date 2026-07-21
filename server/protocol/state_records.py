from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from kungfu_chess.model import Color, PieceKind, PieceState, Position


@dataclass(frozen=True)
class PieceRecord:
    id: str
    color: Color
    kind: PieceKind
    cell: Position
    state: PieceState


@dataclass(frozen=True)
class MotionRecord:
    piece_id: str
    src: Position
    dst: Position
    path: Tuple[Position, ...]
    start_time: float
    duration: float


@dataclass(frozen=True)
class JumpRecord:
    piece_id: str
    cell: Position
    start_time: float
    duration: float
