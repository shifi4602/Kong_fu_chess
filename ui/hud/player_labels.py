"""Tracks whether/who has won, purely from the event bus."""
from __future__ import annotations

from typing import Optional

from kungfu_chess.model import Color
from ui.events.events import Event, GameOver


class PlayerLabels:
    def __init__(self) -> None:
        self._winner: Optional[Color] = None

    def handle(self, event: Event) -> None:
        if isinstance(event, GameOver):
            self._winner = event.winner

    @property
    def winner(self) -> Optional[Color]:
        return self._winner
