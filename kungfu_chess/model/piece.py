from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from .position import Position


class Color(Enum):
    WHITE = 'white'
    BLACK = 'black'


class PieceKind(Enum):
    KING = 'king'
    QUEEN = 'queen'
    ROOK = 'rook'
    BISHOP = 'bishop'
    KNIGHT = 'knight'
    PAWN = 'pawn'


class PieceState(Enum):
    IDLE = 'idle'
    MOVING = 'moving'
    CAPTURED = 'captured'
    JUMPING = 'jumping'


@dataclass
class Piece:
    id: str
    color: Color
    kind: PieceKind
    cell: Position
    state: PieceState = field(default=PieceState.IDLE)
