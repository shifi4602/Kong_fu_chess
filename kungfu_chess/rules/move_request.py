from dataclasses import dataclass

from kungfu_chess.model import Position


@dataclass(frozen=True)
class MoveRequest:
    src: Position
    dst: Position
