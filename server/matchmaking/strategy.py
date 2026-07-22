from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple

from server.transport.connection import Connection


@dataclass(frozen=True)
class Waiter:
    connection: Connection
    username: str
    trace_id: str  # the JoinCommand's trace_id — carried forward to WelcomeEvent (§5)
    rating: int = 1200
    joined_at_ms: int = 0


class MatchmakingStrategy(Protocol):
    def try_match(self, waiting: List[Waiter], now_ms: int) -> Optional[Tuple[Waiter, Waiter]]:
        """Return a pair to seat, or None if nobody's ready to be matched
        yet. Never mutates `waiting` — `Lobby` owns removal. `now_ms` is
        the wall-clock reading at the moment of this join, so a strategy
        can factor in how long each waiter has already been queued (e.g.
        an ELO window that widens over time)."""
        ...


class FirstTwoJoinersStrategy:
    """Stage 1 rule from slide 4: the first two joiners are paired,
    first-come is white. `EloWindowStrategy` below is the stage-4
    replacement behind the same `MatchmakingStrategy` interface — `Lobby`
    doesn't change when the rule does.
    """

    def try_match(self, waiting: List[Waiter], now_ms: int = 0) -> Optional[Tuple[Waiter, Waiter]]:
        if len(waiting) >= 2:
            return waiting[0], waiting[1]
        return None


class EloWindowStrategy:
    """Stage 4's rule (docs/SERVER_PLAN.md §6/§16): pairs the two waiters
    with the closest ratings, but only once their ratings are within an
    acceptable window — ±`base_window` at first, widening by
    `window_growth_per_second` the longer either of them has waited, so a
    queue with many waiters spread across ratings still converges instead
    of matching strictly by arrival order. `max_wait_ms` is a starvation
    guard: once either waiter has been queued that long, any pair
    including them is accepted regardless of rating gap, so nobody waits
    forever just because the pool is thin at their rating.

    Pure function of `(waiting, now_ms)` — no I/O, no side effects on the
    list it's given (`Lobby` owns removal).
    """

    def __init__(
        self,
        base_window: int = 100,
        window_growth_per_second: float = 40.0,
        max_wait_ms: int = 60_000,
    ) -> None:
        self._base_window = base_window
        self._growth_per_second = window_growth_per_second
        self._max_wait_ms = max_wait_ms

    def try_match(self, waiting: List[Waiter], now_ms: int) -> Optional[Tuple[Waiter, Waiter]]:
        best: Optional[Tuple[Waiter, Waiter]] = None
        best_diff: Optional[int] = None

        for i in range(len(waiting)):
            for j in range(i + 1, len(waiting)):
                a, b = waiting[i], waiting[j]
                diff = abs(a.rating - b.rating)
                if not self._eligible(a, b, now_ms, diff):
                    continue
                if best_diff is None or diff < best_diff:
                    # `waiting` is in join order, so `a` (the lower index)
                    # always joined no later than `b` — keeps "first-come
                    # is white" (Lobby destructures the pair as white, black).
                    best, best_diff = (a, b), diff

        return best

    def _eligible(self, a: Waiter, b: Waiter, now_ms: int, diff: int) -> bool:
        if self._elapsed_ms(a, now_ms) >= self._max_wait_ms or self._elapsed_ms(b, now_ms) >= self._max_wait_ms:
            return True
        window = max(self._window_for(a, now_ms), self._window_for(b, now_ms))
        return diff <= window

    def _window_for(self, waiter: Waiter, now_ms: int) -> float:
        elapsed_seconds = self._elapsed_ms(waiter, now_ms) / 1000.0
        return self._base_window + self._growth_per_second * elapsed_seconds

    @staticmethod
    def _elapsed_ms(waiter: Waiter, now_ms: int) -> int:
        return now_ms - waiter.joined_at_ms
