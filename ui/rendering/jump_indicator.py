"""A translucent overlay marking any piece currently in the JUMPING state.

Note: this reacts only to the observable `PieceState.JUMPING` -- it is not
a cooldown countdown. The engine's jump-cooldown timer
(`RealTimeArbiter._jump_ready_at`) is private and never exposed through
`GameSnapshot`; re-deriving it in `ui/` would mean duplicating engine
timing logic, which the architecture explicitly avoids. This is a visual
"airborne" cue, not a "ready again in N seconds" readout.
"""
from __future__ import annotations

from typing import Iterable

from kungfu_chess.model import Position

from .canvas import Canvas
from .coordinate_mapper import CoordinateMapper

_COLOR = (0, 140, 255)
_ALPHA = 110


class JumpIndicator:
    def __init__(self, canvas: Canvas, mapper: CoordinateMapper, cell_size: int) -> None:
        self._canvas = canvas
        self._mapper = mapper
        self._overlay = canvas.blank_image(cell_size, cell_size, color=_COLOR, alpha=_ALPHA)

    def draw(self, jumping_cells: Iterable[Position]) -> None:
        for cell in jumping_cells:
            x, y = self._mapper.cell_top_left(cell)
            self._canvas.blit(self._overlay, x, y)
