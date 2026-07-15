from __future__ import annotations

from typing import Iterable, Tuple

from .canvas import Canvas, ImageHandle

Placement = Tuple[ImageHandle, int, int]


class BoardRenderer:
    """Draws the static background and a list of pre-positioned sprites.
    Purely mechanical -- it has no opinion on where a piece belongs (static
    cell or mid-interpolation); that's decided by whoever builds the
    placement list (e.g. `SceneBuilder`).
    """

    def __init__(self, canvas: Canvas, background: ImageHandle) -> None:
        self._canvas = canvas
        self._background = background

    def draw(self, placements: Iterable[Placement]) -> None:
        self._canvas.begin_frame(self._background)
        for sprite, x, y in placements:
            self._canvas.blit(sprite, x, y)

    def render(self, placements: Iterable[Placement]) -> None:
        """Draw then present in one call, for callers that don't need to
        layer anything (e.g. an FPS overlay) on top before presenting."""
        self.draw(placements)
        self._canvas.present()
