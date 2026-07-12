from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import List

from kungfu_chess.model import Color, GameState, PieceKind, PieceState, Position

from .jump import JumpAction
from .motion import Motion


class IClock(ABC):
    @abstractmethod
    def now(self) -> float:
        pass


class SystemClock(IClock):
    def now(self) -> float:
        return time.monotonic()


class RealTimeArbiter:
    def __init__(
        self,
        clock: IClock,
        travel_duration: float = 1.0,
        jump_duration: float = 1.0,
    ) -> None:
        self._clock = clock
        self._travel_duration = travel_duration
        self._jump_duration = jump_duration
        self._motions: List[Motion] = []
        self._jumps: List[JumpAction] = []

    def start_motion(self, state: GameState, src: Position, dst: Position) -> None:
        piece = state.board.get(src)
        distance = max(abs(dst.row - src.row), abs(dst.col - src.col))
        motion = Motion(
            piece=piece,
            src=src,
            dst=dst,
            start_time=self._clock.now(),
            duration=self._travel_duration * distance,
        )
        piece.state = PieceState.MOVING
        self._motions.append(motion)

    def start_jump(self, state: GameState, position: Position) -> None:
        piece = state.board.get(position)
        jump = JumpAction(
            piece=piece,
            cell=position,
            start_time=self._clock.now(),
            duration=self._jump_duration,
        )
        piece.state = PieceState.JUMPING
        self._jumps.append(jump)

    def tick(self, state: GameState) -> None:
        now = self._clock.now()
        state.current_time = now

        completed_motions: List[Motion] = []
        still_moving: List[Motion] = []
        for motion in self._motions:
            if motion.is_complete(now):
                completed_motions.append(motion)
            else:
                still_moving.append(motion)
        self._motions = still_moving
        for motion in completed_motions:
            self._resolve_arrival(state, motion)

        completed_jumps: List[JumpAction] = []
        still_jumping: List[JumpAction] = []
        for jump in self._jumps:
            if jump.is_complete(now):
                completed_jumps.append(jump)
            else:
                still_jumping.append(jump)
        self._jumps = still_jumping
        for jump in completed_jumps:
            self._land_jump(jump)

    def _resolve_arrival(self, state: GameState, motion: Motion) -> None:
        if motion.piece.state == PieceState.CAPTURED:
            return

        occupant = state.board.get(motion.dst)

        if occupant is not None and occupant.state == PieceState.JUMPING and occupant.color != motion.piece.color:
            if state.board.get(motion.src) is motion.piece:
                state.board.remove(motion.src)
            self._capture(state, motion.piece)
            return

        if occupant is not None and occupant.color == motion.piece.color:
            motion.piece.state = PieceState.IDLE
            return

        if occupant is not None:
            state.board.remove(motion.dst)
            self._capture(state, occupant)

        if state.board.get(motion.src) is motion.piece:
            state.board.remove(motion.src)

        state.board.place(motion.piece, motion.dst)
        motion.piece.state = PieceState.IDLE
        self._maybe_promote(state, motion.piece)

    def _capture(self, state: GameState, piece) -> None:
        piece.state = PieceState.CAPTURED
        if piece.kind == PieceKind.KING:
            state.winner = Color.BLACK if piece.color == Color.WHITE else Color.WHITE

    def _maybe_promote(self, state: GameState, piece) -> None:
        if piece.kind != PieceKind.PAWN:
            return
        last_row = 0 if piece.color == Color.WHITE else state.board.rows - 1
        if piece.cell.row == last_row:
            piece.kind = PieceKind.QUEEN

    def _land_jump(self, jump: JumpAction) -> None:
        jump.piece.state = PieceState.IDLE

    def active_motions(self) -> List[Motion]:
        return list(self._motions)

    def active_jumps(self) -> List[JumpAction]:
        return list(self._jumps)
