from __future__ import annotations

import time
from typing import Protocol


class WallClock(Protocol):
    """A millisecond wall-clock reading. Distinct from `IClock`
    (`kungfu_chess`'s seconds-based, per-session engine clock) and from
    `session/manual_clock.py`'s `ManualClock` — this is real (or faked)
    wall-clock time, read in two deliberately separate places: once per
    scheduler iteration (§9.1) and once per inbound message by
    `handlers/rate_limiter.py` (§9.7) and the join/heartbeat handlers,
    since bounding arrival rate and stamping heartbeat arrival both need
    the instant a message actually arrived, not the last tick's reading.
    """

    def now_ms(self) -> int: ...


class SystemWallClock:
    def now_ms(self) -> int:
        return int(time.monotonic() * 1000)


class FakeWallClock:
    def __init__(self, initial_ms: int = 0) -> None:
        self._ms = initial_ms

    def now_ms(self) -> int:
        return self._ms

    def advance(self, ms: int) -> None:
        self._ms += ms

    def set(self, ms: int) -> None:
        self._ms = ms
