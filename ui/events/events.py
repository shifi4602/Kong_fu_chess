from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from kungfu_chess.model import Color, PieceKind, Position


@dataclass(frozen=True)
class PieceMoved:
    piece_id: str
    color: Color
    kind: PieceKind
    from_cell: Position
    to_cell: Position


@dataclass(frozen=True)
class PieceCaptured:
    piece_id: str
    color: Color
    kind: PieceKind
    cell: Position


@dataclass(frozen=True)
class PiecePromoted:
    piece_id: str
    from_kind: PieceKind
    to_kind: PieceKind
    cell: Position


@dataclass(frozen=True)
class GameOver:
    winner: Color


Event = Union[PieceMoved, PieceCaptured, PiecePromoted, GameOver]
