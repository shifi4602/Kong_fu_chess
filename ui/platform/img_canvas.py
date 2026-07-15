"""The interactive `Canvas` implementation: owns the OpenCV window and its
mouse callback, on top of the shared `ImgFrameBuffer` drawing logic. No
other module in `ui` may import cv2 or `Img` -- they depend on
`ui.rendering.canvas.Canvas` instead.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2

from ui.rendering.canvas import Canvas, MouseButton, MouseEvent

from .img import Img
from .img_frame_buffer import ImgFrameBuffer


class ImgCanvas(Canvas):
    def __init__(self, window_name: str, width: int, height: int) -> None:
        self._window_name = window_name
        self._width = width
        self._height = height
        self._buffer = ImgFrameBuffer()
        self._pending_events: List[MouseEvent] = []
        self._closed = False

        cv2.namedWindow(self._window_name)
        cv2.setMouseCallback(self._window_name, self._on_mouse)

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self._pending_events.append(MouseEvent(MouseButton.LEFT, x, y))
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._pending_events.append(MouseEvent(MouseButton.RIGHT, x, y))

    def load_image(
        self,
        path: Path,
        size: Optional[Tuple[int, int]] = None,
        keep_aspect: bool = False,
    ) -> Img:
        return self._buffer.load_image(path, size=size, keep_aspect=keep_aspect)

    def blank_image(
        self,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (30, 30, 30),
        alpha: Optional[int] = None,
    ) -> Img:
        return self._buffer.blank_image(width, height, color, alpha)

    def image_size(self, image: Img) -> Tuple[int, int]:
        return self._buffer.image_size(image)

    def compose(self, base: Img, overlay: Img, x: int, y: int) -> Img:
        return self._buffer.compose(base, overlay, x, y)

    def begin_frame(self, background: Img) -> None:
        self._buffer.begin_frame(background)

    def blit(self, image: Img, x: int, y: int) -> None:
        self._buffer.blit(image, x, y)

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: float = 0.6,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1,
    ) -> None:
        self._buffer.draw_text(text, x, y, font_size, color, thickness)

    def text_size(self, text: str, font_size: float = 0.6, thickness: int = 1) -> Tuple[int, int]:
        return self._buffer.text_size(text, font_size, thickness)

    def present(self) -> None:
        key = self._buffer.frame.show(self._window_name, wait_ms=1)
        if key == 27:  # Esc
            self._closed = True
        if cv2.getWindowProperty(self._window_name, cv2.WND_PROP_VISIBLE) < 1:
            self._closed = True

    def poll_events(self) -> List[MouseEvent]:
        events, self._pending_events = self._pending_events, []
        return events

    def should_close(self) -> bool:
        return self._closed

    def close(self) -> None:
        cv2.destroyWindow(self._window_name)
