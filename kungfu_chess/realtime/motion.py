from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

from kungfu_chess.model import Piece, Position


@dataclass(frozen=True)
class Motion:
    piece: Piece
    src: Position
    dst: Position
    path: Tuple[Position, ...]
    start_time: float
    duration: float
    sequence: int

    def progress(self, now: float) -> float:
        elapsed = now - self.start_time
        if elapsed <= 0.0:
            return 0.0
        if elapsed >= self.duration:
            return 1.0
        return elapsed / self.duration

    @property
    def step_duration(self) -> float:
        return self.duration / len(self.path)

    def entry_time(self, index: int) -> float:
        return self.start_time + (index + 1) * self.step_duration
