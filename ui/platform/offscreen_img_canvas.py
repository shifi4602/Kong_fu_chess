"""A headless `Canvas`: real Img/cv2 pixels, no window. Used by tests and
dev tools that need to inspect actual rendered output (e.g. dumping a PNG
proof, or replaying a scripted scenario against a FakeClock) without a
display -- as opposed to `FakeCanvas`, which only records draw calls.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2

from ui.rendering.canvas import Canvas, MouseEvent

from .img import Img
from .img_frame_buffer import ImgFrameBuffer


class OffscreenImgCanvas(Canvas):
    def __init__(self) -> None:
        self._buffer = ImgFrameBuffer()

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
        pass

    def poll_events(self) -> List[MouseEvent]:
        return []

    def should_close(self) -> bool:
        return False

    def close(self) -> None:
        pass

    def save(self, path: Path) -> None:
        cv2.imwrite(str(path), self._buffer.frame.img)
