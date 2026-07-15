"""Paces and measures the render loop's own frame rate. Deliberately
separate from the engine's simulation clock (the "two clocks" rule): this
clock never touches `snapshot.current_time` and the engine never touches
this one. Pure arithmetic -- callers supply `now`, nothing here reads a
clock itself, so it's fully unit-testable without real time passing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FrameClock:
    target_fps: float
    _last_tick: Optional[float] = field(default=None, init=False, repr=False)
    _window_start: Optional[float] = field(default=None, init=False, repr=False)
    _frame_count: int = field(default=0, init=False, repr=False)
    _measured_fps: float = field(default=0.0, init=False, repr=False)

    @property
    def frame_duration(self) -> float:
        return 1.0 / self.target_fps

    def tick(self, now: float) -> float:
        """Call once per rendered frame. Returns dt since the previous
        tick and refreshes `measured_fps` once per second of wall time."""
        if self._last_tick is None:
            self._last_tick = now
            self._window_start = now

        dt = now - self._last_tick
        self._last_tick = now

        self._frame_count += 1
        window = now - self._window_start
        if window >= 1.0:
            self._measured_fps = self._frame_count / window
            self._frame_count = 0
            self._window_start = now

        return dt

    @property
    def measured_fps(self) -> float:
        return self._measured_fps
