from enum import Enum
from dataclasses import dataclass

class Color(Enum):
    WHITE = 'w'
    BLACK = 'b'

    @classmethod
    def from_value(cls, val: str):
        for item in cls:
            if item.value == val:
                return item
        raise ValueError(f"Unknown Color: {val}")

class PieceType(Enum):
    KING = 'K'
    QUEEN = 'Q'
    ROOK = 'R'
    BISHOP = 'B'
    KNIGHT = 'N'
    PAWN = 'P'

    @classmethod
    def from_value(cls, val: str):
        for item in cls:
            if item.value == val:
                return item
        raise ValueError(f"Unknown PieceType: {val}")

@dataclass(frozen=True)
class Position:
    row: int
    col: int

@dataclass(frozen=True)
class Piece:
    color: Color
    piece_type: PieceType