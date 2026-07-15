from __future__ import annotations

import pathlib
from typing import Optional, Tuple

import cv2
import numpy as np


class Img:
    """Thin wrapper around a single OpenCV image buffer.

    This -- together with `ImgCanvas` -- is the only code in `ui` that
    touches cv2/numpy pixel data directly. Every other module manipulates
    images through the `Canvas` protocol and opaque `ImageHandle`s.

    Adapted from the reference implementation: `show()` no longer blocks on
    a keypress or tears the window down on every call (a real-time frame
    loop needs a persistent, non-blocking window) -- it now pumps the event
    queue for a short, configurable wait and returns the key code. `blank`
    and `copy` are additions: a frame loop needs a fresh buffer to draw into
    each tick without re-reading a background image from disk.
    """

    def __init__(self) -> None:
        self.img = None

    def read(
        self,
        path: "str | pathlib.Path",
        size: Optional[Tuple[int, int]] = None,
        keep_aspect: bool = False,
        interpolation: int = cv2.INTER_AREA,
    ) -> "Img":
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]

            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h

            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        return self

    @classmethod
    def blank(
        cls,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (30, 30, 30),
        alpha: Optional[int] = None,
    ) -> "Img":
        image = cls()
        if alpha is None:
            image.img = np.full((height, width, 3), color, dtype=np.uint8)
        else:
            b, g, r = color
            image.img = np.full((height, width, 4), (b, g, r, alpha), dtype=np.uint8)
        return image

    def copy(self) -> "Img":
        clone = Img()
        clone.img = self.img.copy()
        return clone

    def draw_on(self, other_img: "Img", x: int, y: int) -> None:
        """Composite `self` onto `other_img` at (x, y), alpha-blending if
        `self` has 4 channels.

        Unlike the reference implementation, this never mutates `self.img`
        to match `other_img`'s channel count: `SpriteLoader` caches `Img`
        instances, so converting a 4-channel sprite down to 3 (dropping
        alpha) in place would permanently destroy that sprite's
        transparency the first time it was drawn onto a 3-channel
        background -- every later frame would reuse the now-opaque cached
        image. Blending is done per-channel against however many color
        channels the destination actually has instead.
        """
        if self.img is None or other_img.img is None:
            raise ValueError("Both images must be loaded before drawing.")

        h, w = self.img.shape[:2]
        H, W = other_img.img.shape[:2]

        if y + h > H or x + w > W:
            raise ValueError("Logo does not fit at the specified position.")

        roi = other_img.img[y:y + h, x:x + w]
        channels = min(3, roi.shape[2])

        if self.img.shape[2] == 4:
            alpha = self.img[..., 3] / 255.0
            for c in range(channels):
                roi[..., c] = (1 - alpha) * roi[..., c] + alpha * self.img[..., c]
        else:
            roi[..., :channels] = self.img[..., :channels]

    def put_text(
        self,
        txt: str,
        x: int,
        y: int,
        font_size: float,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1,
    ) -> None:
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(
            self.img, txt, (x, y),
            cv2.FONT_HERSHEY_SIMPLEX, font_size,
            color, thickness, cv2.LINE_AA,
        )

    def show(self, window_name: str = "Kung Fu Chess", wait_ms: int = 1) -> int:
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow(window_name, self.img)
        return cv2.waitKey(wait_ms)

    @staticmethod
    def text_size(text: str, font_size: float = 0.6, thickness: int = 1) -> Tuple[int, int]:
        (width, height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_size, thickness
        )
        return width, height + baseline
