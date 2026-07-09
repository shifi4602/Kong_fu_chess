from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import List

from kungfu_chess.model.game_state import GameState
from kungfu_chess.model.piece import PieceState
from kungfu_chess.model.position import Position

from .motion import Motion


class IClock(ABC):
    @abstractmethod
    def now(self) -> float:
        pass


class SystemClock(IClock):
    def now(self) -> float:
        return time.monotonic()


class RealTimeArbiter:
    def __init__(self, clock: IClock, travel_duration: float = 1.0) -> None:
        self._clock = clock
        self._travel_duration = travel_duration
        self._motions: List[Motion] = []

    def start_motion(self, state: GameState, src: Position, dst: Position) -> None:
        piece = state.board.get(src)
        motion = Motion(
            piece=piece,
            src=src,
            dst=dst,
            start_time=self._clock.now(),
            duration=self._travel_duration,
        )
        piece.state = PieceState.MOVING
        self._motions.append(motion)

    def tick(self, state: GameState) -> None:
        now = self._clock.now()
        state.current_time = now
        still_moving: List[Motion] = []
        for motion in self._motions:
            if motion.is_complete(now):
                self._resolve_arrival(state, motion)
            else:
                still_moving.append(motion)
        self._motions = still_moving

    def _resolve_arrival(self, state: GameState, motion: Motion) -> None:
        occupant = state.board.get(motion.dst)
        if occupant is not None:
            state.board.remove(motion.dst)
            occupant.state = PieceState.CAPTURED

        if state.board.get(motion.src) is motion.piece:
            state.board.remove(motion.src)

        state.board.place(motion.piece, motion.dst)
        motion.piece.state = PieceState.IDLE

    def active_motions(self) -> List[Motion]:
        return list(self._motions)
