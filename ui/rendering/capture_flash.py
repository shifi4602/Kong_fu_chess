"""A brief fading flash over a cell where a capture just happened. Fed
directly by the frame loop (not the event bus) because it needs `now` to
time the fade -- the generic EventBus is HUD-only and carries no timing.
"""
from __future__ import annotations

from typing import List, Tuple

from kungfu_chess.model import Position

from .canvas import Canvas
from .coordinate_mapper import CoordinateMapper

_COLOR = (0, 0, 220)
_PEAK_ALPHA = 190


class CaptureFlash:
    def __init__(
        self, canvas: Canvas, mapper: CoordinateMapper, cell_size: int, duration: float = 0.4
    ) -> None:
        self._canvas = canvas
        self._mapper = mapper
        self._cell_size = cell_size
        self._duration = duration
        self._active: List[Tuple[Position, float]] = []

    def record(self, cell: Position, now: float) -> None:
        self._active.append((cell, now))

    def draw(self, now: float) -> None:
        still_active: List[Tuple[Position, float]] = []
        for cell, started_at in self._active:
            elapsed = now - started_at
            if elapsed >= self._duration:
                continue
            still_active.append((cell, started_at))

            fade = 1.0 - (elapsed / self._duration)
            overlay = self._canvas.blank_image(
                self._cell_size, self._cell_size, color=_COLOR, alpha=int(_PEAK_ALPHA * fade)
            )
            x, y = self._mapper.cell_top_left(cell)
            self._canvas.blit(overlay, x, y)

        self._active = still_active
