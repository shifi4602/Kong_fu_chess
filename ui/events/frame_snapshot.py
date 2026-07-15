"""A lightweight, pure record of "what we care about for diffing" a
GameSnapshot into. Not to be confused with the interpolation path (Stage
6), which deliberately never freezes a snapshot -- this exists purely to
detect discrete events (capture/promotion/game-over) between two ticks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from kungfu_chess.engine import GameSnapshot
from kungfu_chess.model import Color, PieceKind, PieceState, Position


@dataclass(frozen=True)
class PieceRecord:
    color: Color
    kind: PieceKind
    state: PieceState
    cell: Position


@dataclass(frozen=True)
class FrameSnapshot:
    pieces: Dict[str, PieceRecord]
    winner: Optional[Color]


def capture_frame_snapshot(snapshot: GameSnapshot) -> FrameSnapshot:
    pieces = {
        piece.id: PieceRecord(piece.color, piece.kind, piece.state, piece.cell)
        for piece in snapshot.board.all_pieces()
    }
    return FrameSnapshot(pieces=pieces, winner=snapshot.winner)
