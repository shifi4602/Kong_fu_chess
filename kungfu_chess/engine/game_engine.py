from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from kungfu_chess.model.board import Board
from kungfu_chess.model.game_state import GameState
from kungfu_chess.model.piece import Color, PieceKind
from kungfu_chess.realtime.motion import Motion
from kungfu_chess.realtime.real_time_arbiter import RealTimeArbiter
from kungfu_chess.rules.move_request import MoveRequest
from kungfu_chess.rules.rule_engine import RuleEngine


@dataclass(frozen=True)
class GameSnapshot:
    board: Board
    motions: List[Motion]
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
        if self._rule_engine.can_move(self._state, request):
            self._arbiter.start_motion(self._state, request.src, request.dst)
            return True
        return False

    def tick(self) -> None:
        if self._state.is_over:
            return
        self._arbiter.tick(self._state)
        self._check_game_over()

    def _check_game_over(self) -> None:
        if self._state.is_over:
            return

        white_has_king = False
        black_has_king = False

        for piece in self._state.board.all_pieces():
            if piece.kind == PieceKind.KING:
                if piece.color == Color.WHITE:
                    white_has_king = True
                if piece.color == Color.BLACK:
                    black_has_king = True

        if not white_has_king:
            self._state.winner = Color.BLACK
            return
        if not black_has_king:
            self._state.winner = Color.WHITE
            return

    def get_snapshot(self) -> GameSnapshot:
        return GameSnapshot(
            board=self._state.board,
            motions=self._arbiter.active_motions(),
            winner=self._state.winner,
            current_time=self._state.current_time,
        )
