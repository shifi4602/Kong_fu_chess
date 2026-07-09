from dataclasses import dataclass, field
from typing import Optional

from .board import Board
from .piece import Color


@dataclass
class GameState:
    board: Board
    current_time: float = 0.0
    winner: Optional[Color] = None

    @property
    def is_over(self) -> bool:
        return self.winner is not None
