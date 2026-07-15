from __future__ import annotations

from typing import Tuple

from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Position


class CoordinateMapper:
    """Wraps the engine's own `BoardMapper` and adds the pixel arithmetic
    needed to place a sprite inside a cell -- nothing here knows about
    chess rules or the rendering backend.
    """

    def __init__(self, mapper: BoardMapper, cell_size: int) -> None:
        self._mapper = mapper
        self._cell_size = cell_size

    def cell_top_left(self, pos: Position) -> Tuple[int, int]:
        return self._mapper.position_to_pixel(pos)

    def anchor_at(self, pixel: Tuple[float, float], sprite_size: Tuple[int, int]) -> Tuple[int, int]:
        """Top-left pixel to blit a sprite so it's horizontally centered
        and bottom-aligned within a cell whose own top-left is `pixel` --
        `pixel` may be a static cell or an interpolated in-between point."""
        px, py = pixel
        sprite_w, sprite_h = sprite_size
        x = px + (self._cell_size - sprite_w) / 2
        y = py + (self._cell_size - sprite_h)
        return int(round(x)), int(round(y))

    def sprite_anchor(self, pos: Position, sprite_size: Tuple[int, int]) -> Tuple[int, int]:
        """Top-left pixel to blit a sprite so it's horizontally centered
        and bottom-aligned within the cell at `pos`."""
        return self.anchor_at(self.cell_top_left(pos), sprite_size)
