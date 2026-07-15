"""Minimal Observer-pattern pub/sub. Intentionally generic and one-way:
publishers (the frame loop) don't know or care who's listening. Stage 8's
HUD panels are the only intended subscribers.
"""
from __future__ import annotations

from typing import Callable, Iterable, List

from .events import Event

Handler = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: List[Handler] = []

    def subscribe(self, handler: Handler) -> None:
        self._handlers.append(handler)

    def publish(self, events: Iterable[Event]) -> None:
        for event in events:
            for handler in self._handlers:
                handler(event)
