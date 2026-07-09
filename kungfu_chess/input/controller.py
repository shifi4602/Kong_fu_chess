from typing import Optional

from kungfu_chess.engine import GameEngine
from kungfu_chess.model import PieceState, Position
from kungfu_chess.rules import MoveRequest
from .board_mapper import BoardMapper


class Controller:
    def __init__(self, engine: GameEngine, mapper: BoardMapper) -> None:
        self._engine = engine
        self._mapper = mapper
        self._selected: Optional[Position] = None

    @property
    def selected(self) -> Optional[Position]:
        return self._selected

    def on_tick(self) -> None:
        self._engine.tick()

    def on_click(self, x: int, y: int) -> None:
        pos = self._mapper.pixel_to_position(x, y)
        if pos is None:
            return

        if self._selected is None:
            piece = self._engine.get_snapshot().board.get(pos)
            if piece is None:
                return
            if piece.state != PieceState.IDLE:
                return
            self._selected = pos
            return

        if pos == self._selected:
            self._selected = None
            return

        if self._engine.request_move(MoveRequest(self._selected, pos)):
            self._selected = None
            return

        piece = self._engine.get_snapshot().board.get(pos)
        if piece is not None and piece.state == PieceState.IDLE:
            self._selected = pos
            return

        self._selected = None
