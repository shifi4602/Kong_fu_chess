from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List

Handler = Callable[[Any], None]


class EventBus:
    """A typed, multi-topic generalization of `ui/events/event_bus.py`'s
    Observer bus — the backbone of the whole server (§3), not a one-off
    wiring for a sidebar. Deliberately synchronous: `publish`/`subscribe`
    are plain function calls, never `async def` (§9.2). That's what makes
    `GameSession.advance(now_ms)` testable with a bare integer, and it
    matches the existing `ui/events/event_bus.py`, which is already
    synchronous.
    """

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers[topic].append(handler)

    def publish(self, topic: str, record: Any) -> None:
        for handler in self._handlers[topic]:
            handler(record)
