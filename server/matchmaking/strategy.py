from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple

from server.transport.connection import Connection


@dataclass(frozen=True)
class Waiter:
    connection: Connection
    username: str
    trace_id: str  # the JoinCommand's trace_id — carried forward to WelcomeEvent (§5)


class MatchmakingStrategy(Protocol):
    def try_match(self, waiting: List[Waiter]) -> Optional[Tuple[Waiter, Waiter]]:
        """Return a pair to seat, or None if nobody's ready to be matched
        yet. Never mutates `waiting` — `Lobby` owns removal."""
        ...


class FirstTwoJoinersStrategy:
    """Stage 1 rule from slide 4: the first two joiners are paired,
    first-come is white. Slide 6 replaces this with an ELO-window
    strategy behind the same `MatchmakingStrategy` interface — `Lobby`
    doesn't change when the rule does.
    """

    def try_match(self, waiting: List[Waiter]) -> Optional[Tuple[Waiter, Waiter]]:
        if len(waiting) >= 2:
            return waiting[0], waiting[1]
        return None
