from __future__ import annotations
from dataclasses import dataclass

from kungfu_chess.model.piece import Piece
from kungfu_chess.model.position import Position


@dataclass(frozen=True)
class Motion:
    piece: Piece
    src: Position
    dst: Position
    start_time: float
    duration: float

    def is_complete(self, now: float) -> bool:
        if now >= self.start_time + self.duration:
            return True
        return False

    def progress(self, now: float) -> float:
        elapsed = now - self.start_time
        if elapsed <= 0.0:
            return 0.0
        if elapsed >= self.duration:
            return 1.0
        return elapsed / self.duration
