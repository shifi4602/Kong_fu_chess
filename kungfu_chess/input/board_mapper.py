from typing import Optional, Tuple

from kungfu_chess.model.position import Position


class BoardMapper:
    def __init__(self, cell_size: int, rows: int = 8, cols: int = 8) -> None:
        self._cell_size = cell_size
        self._rows = rows
        self._cols = cols

    def pixel_to_position(self, x: int, y: int) -> Optional[Position]:
        row = y // self._cell_size
        col = x // self._cell_size
        if row < 0 or row >= self._rows:
            return None
        if col < 0 or col >= self._cols:
            return None
        return Position(row, col)

    def position_to_pixel(self, pos: Position) -> Tuple[int, int]:
        return (pos.col * self._cell_size, pos.row * self._cell_size)
