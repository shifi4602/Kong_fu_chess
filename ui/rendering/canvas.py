"""The Canvas boundary: the single seam every rendering/animation/input
module in `ui` is allowed to depend on.

No module outside `ui/platform/` may import the concrete drawing backend
(`Img`/cv2) -- they depend on this Protocol instead (Dependency Inversion),
so the backend can be swapped, or a `FakeCanvas` substituted in tests, by
writing a new implementation of this Protocol only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Protocol, Tuple, runtime_checkable

# Opaque handle returned by Canvas.load_image / Canvas.blank_image. Callers
# store and pass it back to blit() -- they never look inside it. Concretely
# it is an `Img` in the OpenCV backend, but nothing outside ui/platform/
# is allowed to know that.
ImageHandle = Any


class MouseButton(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class MouseEvent:
    button: MouseButton
    x: int
    y: int


@runtime_checkable
class Canvas(Protocol):
    def load_image(
        self,
        path: Path,
        size: Optional[Tuple[int, int]] = None,
        keep_aspect: bool = False,
    ) -> ImageHandle:
        """Load an image file into a handle. Callers should cache the
        result themselves rather than reloading every frame."""
        ...

    def blank_image(
        self,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (30, 30, 30),
        alpha: Optional[int] = None,
    ) -> ImageHandle:
        """A solid-color image handle, for backgrounds/placeholders that
        don't come from a file. `alpha` (0-255) makes it translucent when
        blitted -- e.g. a selection highlight that doesn't hide the piece
        underneath."""
        ...

    def image_size(self, image: ImageHandle) -> Tuple[int, int]:
        """(width, height) of a loaded image handle, without exposing what
        the handle actually is."""
        ...

    def compose(self, base: ImageHandle, overlay: ImageHandle, x: int, y: int) -> ImageHandle:
        """A new handle: `overlay` blitted onto a copy of `base` at (x, y).
        For prebaking a fixed composite once at startup (e.g. board image +
        sidebar panel) rather than every frame."""
        ...

    def begin_frame(self, background: ImageHandle) -> None:
        """Start a new frame using `background` as the base buffer."""
        ...

    def blit(self, image: ImageHandle, x: int, y: int) -> None:
        """Composite `image` onto the current frame at pixel (x, y)."""
        ...

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: float = 0.6,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1,
    ) -> None:
        """Draw text directly onto the current frame."""
        ...

    def text_size(self, text: str, font_size: float = 0.6, thickness: int = 1) -> Tuple[int, int]:
        """(width, height) in pixels the text would occupy if drawn with
        `draw_text` -- for centering, without drawing anything."""
        ...

    def present(self) -> None:
        """Show the current frame and pump the window's event queue for one
        tick. Must never block waiting for a keypress."""
        ...

    def poll_events(self) -> List[MouseEvent]:
        """Drain and return mouse events queued since the last poll."""
        ...

    def should_close(self) -> bool:
        """True once the user has asked to close the window (Esc / [x])."""
        ...

    def close(self) -> None:
        """Release window/backend resources. Call once at shutdown."""
        ...
