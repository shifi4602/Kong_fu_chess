"""Drawing logic shared by every Img-backed Canvas: the parts of `Canvas`
that don't depend on a live window. `ImgCanvas` (interactive) and
`OffscreenImgCanvas` (headless) both compose this instead of duplicating
the same `Img` calls.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .img import Img


class ImgFrameBuffer:
    def __init__(self) -> None:
        self._frame: Optional[Img] = None

    def load_image(
        self,
        path: Path,
        size: Optional[Tuple[int, int]] = None,
        keep_aspect: bool = False,
    ) -> Img:
        return Img().read(path, size=size, keep_aspect=keep_aspect)

    def blank_image(
        self,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (30, 30, 30),
        alpha: Optional[int] = None,
    ) -> Img:
        return Img.blank(width, height, color, alpha)

    def image_size(self, image: Img) -> Tuple[int, int]:
        h, w = image.img.shape[:2]
        return w, h

    def compose(self, base: Img, overlay: Img, x: int, y: int) -> Img:
        result = base.copy()
        overlay.draw_on(result, x, y)
        return result

    def begin_frame(self, background: Img) -> None:
        self._frame = background.copy()

    def blit(self, image: Img, x: int, y: int) -> None:
        if self._frame is None:
            raise RuntimeError("begin_frame() must be called before blit()")
        image.draw_on(self._frame, x, y)

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: float = 0.6,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1,
    ) -> None:
        if self._frame is None:
            raise RuntimeError("begin_frame() must be called before draw_text()")
        self._frame.put_text(text, x, y, font_size, color, thickness)

    def text_size(self, text: str, font_size: float = 0.6, thickness: int = 1) -> Tuple[int, int]:
        return Img.text_size(text, font_size, thickness)

    @property
    def frame(self) -> Img:
        if self._frame is None:
            raise RuntimeError("begin_frame() must be called first")
        return self._frame
