"""Pure frame-index arithmetic: given how long an animation has been
playing, decide which frame to show and whether a non-looping animation
has run out of frames. No cv2, no engine coupling.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnimClock:
    frames_per_sec: float
    is_loop: bool

    def frame_index(self, elapsed: float, frame_count: int) -> int:
        if frame_count <= 0:
            return 0
        raw_index = int(elapsed * self.frames_per_sec)
        if self.is_loop:
            return raw_index % frame_count
        return min(raw_index, frame_count - 1)

    def is_finished(self, elapsed: float, frame_count: int) -> bool:
        if self.is_loop:
            return False
        return int(elapsed * self.frames_per_sec) >= frame_count
