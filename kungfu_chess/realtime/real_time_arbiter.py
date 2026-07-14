from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

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


def _build_path(src: Position, dst: Position) -> Tuple[Position, ...]:
    diff_r = dst.row - src.row
    diff_c = dst.col - src.col

    is_straight_or_diagonal = diff_r == 0 or diff_c == 0 or abs(diff_r) == abs(diff_c)
    if not is_straight_or_diagonal:
        return (dst,)

    steps = max(abs(diff_r), abs(diff_c))
    dr = 0 if diff_r == 0 else (1 if diff_r > 0 else -1)
    dc = 0 if diff_c == 0 else (1 if diff_c > 0 else -1)

    path = []
    r, c = src.row, src.col
    for _ in range(steps):
        r += dr
        c += dc
        path.append(Position(r, c))
    return tuple(path)


class RealTimeArbiter:
    def __init__(
        self,
        clock: IClock,
        travel_duration: float = 1.0,
        jump_duration: float = 1.0,
        jump_cooldown: float = 1.0,
    ) -> None:
        self._clock = clock
        self._travel_duration = travel_duration
        self._jump_duration = jump_duration
        self._jump_cooldown = jump_cooldown
        self._motions: List[Motion] = []
        self._jumps: List[JumpAction] = []
        self._jump_ready_at: Dict[str, float] = {}
        self._motion_progress: Dict[int, int] = {}
        self._motion_sequence: int = 0

    def start_motion(self, state: GameState, src: Position, dst: Position) -> None:
        piece = state.board.get(src)
        distance = max(abs(dst.row - src.row), abs(dst.col - src.col))
        path = _build_path(src, dst)
        sequence = self._motion_sequence
        self._motion_sequence += 1
        motion = Motion(
            piece=piece,
            src=src,
            dst=dst,
            path=path,
            start_time=self._clock.now(),
            duration=self._travel_duration * distance,
            sequence=sequence,
        )
        piece.state = PieceState.MOVING
        self._motion_progress[id(motion)] = -1
        self._motions.append(motion)

    def can_jump(self, piece) -> bool:
        ready_at = self._jump_ready_at.get(piece.id)
        if ready_at is None:
            return True
        return self._clock.now() >= ready_at

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

        self._resolve_motions(state, now)

        completed_jumps: List[JumpAction] = []
        still_jumping: List[JumpAction] = []
        for jump in self._jumps:
            if jump.is_complete(now):
                completed_jumps.append(jump)
            else:
                still_jumping.append(jump)
        self._jumps = still_jumping
        for jump in completed_jumps:
            self._land_jump(jump, now)

    def _resolve_motions(self, state: GameState, now: float) -> None:
        while True:
            motion = self._earliest_pending_motion(now)
            if motion is None:
                return
            self._resolve_motion_step(state, motion)

    def _earliest_pending_motion(self, now: float) -> Optional[Motion]:
        best: Optional[Motion] = None
        best_key: Optional[Tuple[float, int]] = None
        for motion in self._motions:
            next_index = self._motion_progress[id(motion)] + 1
            entry_time = motion.entry_time(next_index)
            if entry_time > now:
                continue
            key = (entry_time, motion.sequence)
            if best_key is None or key < best_key:
                best_key = key
                best = motion
        return best

    def _resolve_motion_step(self, state: GameState, motion: Motion) -> None:
        piece = motion.piece
        index = self._motion_progress[id(motion)] + 1
        cell = motion.path[index]
        resident, resident_motion = self._resident_at(state, cell, piece)

        if resident is None:
            self._motion_progress[id(motion)] = index
            if index == len(motion.path) - 1:
                self._settle(state, motion, cell)
            return

        if resident.state == PieceState.JUMPING and resident.color != piece.color:
            if state.board.get(motion.src) is piece:
                state.board.remove(motion.src)
            self._capture(state, piece)
            self._cancel_motion(motion)
            return

        if resident.color != piece.color:
            self._remove_resident(state, resident, resident_motion)
            self._capture(state, resident)
            self._settle(state, motion, cell)
            return

        stop_cell = motion.path[index - 1] if index > 0 else motion.src
        self._settle(state, motion, stop_cell)

    def _resident_at(
        self, state: GameState, cell: Position, exclude_piece
    ) -> Tuple[Optional[object], Optional[Motion]]:
        board_piece = state.board.get(cell)
        if board_piece is not None and board_piece is not exclude_piece:
            return board_piece, None

        for other in self._motions:
            if other.piece is exclude_piece:
                continue
            other_index = self._motion_progress[id(other)]
            if other_index >= 0 and other.path[other_index] == cell:
                return other.piece, other

        return None, None

    def _remove_resident(
        self, state: GameState, resident, resident_motion: Optional[Motion]
    ) -> None:
        if resident_motion is not None:
            if state.board.get(resident_motion.src) is resident:
                state.board.remove(resident_motion.src)
            self._cancel_motion(resident_motion)
        else:
            if state.board.get(resident.cell) is resident:
                state.board.remove(resident.cell)

    def _settle(self, state: GameState, motion: Motion, cell: Position) -> None:
        piece = motion.piece
        if state.board.get(motion.src) is piece:
            state.board.remove(motion.src)
        state.board.place(piece, cell)
        piece.state = PieceState.IDLE
        self._maybe_promote(state, piece)
        self._cancel_motion(motion)

    def _cancel_motion(self, motion: Motion) -> None:
        self._motion_progress.pop(id(motion), None)
        self._motions = [m for m in self._motions if m is not motion]

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

    def _land_jump(self, jump: JumpAction, now: float) -> None:
        jump.piece.state = PieceState.IDLE
        self._jump_ready_at[jump.piece.id] = now + self._jump_cooldown

    def active_motions(self) -> List[Motion]:
        return list(self._motions)

    def active_jumps(self) -> List[JumpAction]:
        return list(self._jumps)
