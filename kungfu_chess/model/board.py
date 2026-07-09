from typing import Dict, Iterator, List, Optional, Tuple

from .piece import Color, Piece
from .position import Position


class Board:
    def __init__(self, rows: int = 8, cols: int = 8):
        self.rows = rows
        self.cols = cols
        self._grid: Dict[Position, Piece] = {}

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def get(self, pos: Position) -> Optional[Piece]:
        return self._grid.get(pos)

    def place(self, piece: Piece, pos: Position) -> None:
        if not self.in_bounds(pos):
            raise ValueError(f"{pos} is out of bounds for a {self.rows}x{self.cols} board")
        self._grid[pos] = piece
        piece.cell = pos

    def remove(self, pos: Position) -> Optional[Piece]:
        return self._grid.pop(pos, None)

    def is_occupied(self, pos: Position) -> bool:
        return pos in self._grid

    def all_pieces(self) -> List[Piece]:
        return list(self._grid.values())

    def pieces_by_color(self, color: Color) -> List[Piece]:
        return [p for p in self._grid.values() if p.color == color]

    def __iter__(self) -> Iterator[Tuple[Position, Piece]]:
        return iter(self._grid.items())

    def __repr__(self) -> str:
        return f"Board({self.rows}x{self.cols}, {len(self._grid)} pieces)"
