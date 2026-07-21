from __future__ import annotations

from kungfu_chess.realtime import IClock


class ManualClock(IClock):
    """A third `IClock` implementation, alongside `SystemClock` and the
    various `FakeClock`s already in the repo — driven by `.set(engine_ms)`
    once per tick from `GameSession.advance` rather than by wall-clock
    reads. `IClock` speaks seconds throughout `kungfu_chess`; the wire
    protocol and scheduler speak milliseconds — this is the one place that
    conversion happens.
    """

    def __init__(self, initial_ms: int = 0) -> None:
        self._ms = initial_ms

    def set(self, engine_ms: int) -> None:
        self._ms = engine_ms

    def now(self) -> float:
        return self._ms / 1000.0
