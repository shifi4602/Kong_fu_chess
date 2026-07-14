from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from kungfu_chess.model import Board, Color, GameState, PieceState, Position
from kungfu_chess.realtime import JumpAction, Motion, RealTimeArbiter
from kungfu_chess.rules import MoveRequest, RuleEngine


@dataclass(frozen=True)
class GameSnapshot:
    board: Board
    motions: List[Motion]
    jumps: List[JumpAction]
    winner: Optional[Color]
    current_time: float

    @property
    def is_over(self) -> bool:
        if self.winner is not None:
            return True
        return False


class GameEngine:
    def __init__(
        self,
        state: GameState,
        rule_engine: RuleEngine,
        arbiter: RealTimeArbiter,
    ) -> None:
        self._state = state
        self._rule_engine = rule_engine
        self._arbiter = arbiter

    def request_move(self, request: MoveRequest) -> bool:
        if self._state.is_over:
            return False
        if self._rule_engine.is_valid(self._state, request):
            self._arbiter.start_motion(self._state, request.src, request.dst)
            return True
        return False

    def request_jump(self, position: Position) -> bool:
        if self._state.is_over:
            return False
        piece = self._state.board.get(position)
        if piece is None:
            return False
        if piece.state != PieceState.IDLE:
            return False
        if not self._arbiter.can_jump(piece):
            return False
        self._arbiter.start_jump(self._state, position)
        return True

    def tick(self) -> None:
        if self._state.is_over:
            return
        self._arbiter.tick(self._state)

    def get_snapshot(self) -> GameSnapshot:
        return GameSnapshot(
            board=self._state.board,
            motions=self._arbiter.active_motions(),
            jumps=self._arbiter.active_jumps(),
            winner=self._state.winner,
            current_time=self._state.current_time,
        )
