
from __future__ import annotations
from dataclasses import dataclass

from kungfu_chess.model import Piece, Position


@dataclass(frozen=True)
class JumpAction:
    piece: Piece
    cell: Position
    start_time: float
    duration: float

    def is_complete(self, now: float) -> bool:
        if now >= self.start_time + self.duration:
            return True
        return False
