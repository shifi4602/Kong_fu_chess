from __future__ import annotations

from typing import Optional, Tuple

from kungfu_chess.model import Position

from .canvas import Canvas, ImageHandle
from .coordinate_mapper import CoordinateMapper


class HighlightRenderer:
    """Draws a translucent overlay over the currently selected cell. Reads
    `Controller.selected` (via the caller) -- no selection logic lives
    here, just where to draw it.
    """

    def __init__(
        self,
        canvas: Canvas,
        mapper: CoordinateMapper,
        cell_size: int,
        color: Tuple[int, int, int] = (0, 255, 255),
        alpha: int = 90,
    ) -> None:
        self._canvas = canvas
        self._mapper = mapper
        self._highlight: ImageHandle = canvas.blank_image(cell_size, cell_size, color=color, alpha=alpha)

    def draw(self, selected: Optional[Position]) -> None:
        if selected is None:
            return
        x, y = self._mapper.cell_top_left(selected)
        self._canvas.blit(self._highlight, x, y)
