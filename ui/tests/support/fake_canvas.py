"""Test double for `Canvas`: records every draw call instead of touching a
real backend, so renderer/animation logic can be asserted against without
cv2 or a display.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ui.rendering.canvas import MouseEvent


@dataclass(frozen=True)
class FakeImage:
    path: Optional[Path]
    size: Tuple[int, int]


class FakeCanvas:
    def __init__(self) -> None:
        self.load_image_calls: List[Path] = []
        self.begin_frame_calls: List[FakeImage] = []
        self.blit_calls: List[Tuple[FakeImage, int, int]] = []
        self.draw_text_calls: List[Tuple[str, int, int]] = []
        self.present_count: int = 0
        self.closed: bool = False
        self._should_close: bool = False
        self._events: List[MouseEvent] = []

    def load_image(
        self,
        path: Path,
        size: Optional[Tuple[int, int]] = None,
        keep_aspect: bool = False,
    ) -> FakeImage:
        self.load_image_calls.append(Path(path))
        return FakeImage(path=Path(path), size=size or (0, 0))

    def blank_image(
        self,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (30, 30, 30),
        alpha: Optional[int] = None,
    ) -> FakeImage:
        return FakeImage(path=None, size=(width, height))

    def image_size(self, image: FakeImage) -> Tuple[int, int]:
        return image.size

    def compose(self, base: FakeImage, overlay: FakeImage, x: int, y: int) -> FakeImage:
        return FakeImage(path=base.path, size=base.size)

    def begin_frame(self, background: FakeImage) -> None:
        self.begin_frame_calls.append(background)

    def blit(self, image: FakeImage, x: int, y: int) -> None:
        self.blit_calls.append((image, x, y))

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: float = 0.6,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1,
    ) -> None:
        self.draw_text_calls.append((text, x, y))

    def text_size(self, text: str, font_size: float = 0.6, thickness: int = 1) -> Tuple[int, int]:
        # Deterministic stand-in for cv2.getTextSize: doesn't need to be
        # pixel-accurate, just proportional to text length and font size.
        return int(len(text) * 12 * font_size), int(20 * font_size)

    def present(self) -> None:
        self.present_count += 1

    def poll_events(self) -> List[MouseEvent]:
        events, self._events = self._events, []
        return events

    def should_close(self) -> bool:
        return self._should_close

    def close(self) -> None:
        self.closed = True

    def queue_event(self, event: MouseEvent) -> None:
        """Test helper -- not part of the Canvas protocol."""
        self._events.append(event)
