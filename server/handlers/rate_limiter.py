from __future__ import annotations

from typing import Dict

from server.clock import WallClock


class RateLimiter:
    """Per-connection token bucket, consulted by the dispatcher before a
    command ever reaches `session.enqueue()` (§9.7). Bounds *arrival*
    rate, so it takes its own small injectable `WallClock` rather than
    the `now_ms`-driven `tick_all` loop's reading (§9.1) — batching this
    check onto the tick clock would defeat the point.
    """

    def __init__(self, max_per_second: float, burst: int, clock: WallClock) -> None:
        self._max_per_second = max_per_second
        self._burst = burst
        self._clock = clock
        self._tokens: Dict[str, float] = {}
        self._last_refill_ms: Dict[str, int] = {}

    def allow(self, connection_id: str) -> bool:
        now_ms = self._clock.now_ms()
        last_ms = self._last_refill_ms.get(connection_id, now_ms)
        tokens = self._tokens.get(connection_id, float(self._burst))

        elapsed_s = max(0, now_ms - last_ms) / 1000.0
        tokens = min(self._burst, tokens + elapsed_s * self._max_per_second)
        self._last_refill_ms[connection_id] = now_ms

        if tokens < 1.0:
            self._tokens[connection_id] = tokens
            return False

        self._tokens[connection_id] = tokens - 1.0
        return True
