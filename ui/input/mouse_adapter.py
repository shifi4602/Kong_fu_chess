"""The one place in `ui` that talks to the engine's own input adapter
(`kungfu_chess.input.Controller`). Translates backend-agnostic `MouseEvent`s
from a `Canvas` into `on_click`/`on_jump` calls -- no selection, move, or
jump logic is reimplemented here; the engine's Controller already owns all
of that.
"""
from __future__ import annotations

from typing import List

from kungfu_chess.input import Controller
from ui.rendering.canvas import MouseButton, MouseEvent


class MouseAdapter:
    def __init__(self, controller: Controller) -> None:
        self._controller = controller

    def handle(self, events: List[MouseEvent]) -> None:
        for event in events:
            if event.button == MouseButton.LEFT:
                self._controller.on_click(event.x, event.y)
            elif event.button == MouseButton.RIGHT:
                self._controller.on_jump(event.x, event.y)
