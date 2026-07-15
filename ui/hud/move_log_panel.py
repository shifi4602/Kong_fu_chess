"""Keeps a scrolling human-readable log of moves/captures/promotions, fed
purely by events -- it never inspects the board or engine state directly.
"""
from __future__ import annotations

from typing import List

from kungfu_chess.model import Position
from ui.events.events import Event, PieceCaptured, PieceMoved, PiecePromoted


def _cell_label(cell: Position, board_rows: int) -> str:
    file_letter = chr(ord("a") + cell.col)
    rank_number = board_rows - cell.row
    return f"{file_letter}{rank_number}"


class MoveLogPanel:
    def __init__(self, board_rows: int, max_entries: int = 100) -> None:
        self._board_rows = board_rows
        self._max_entries = max_entries
        self._entries: List[str] = []

    def handle(self, event: Event) -> None:
        if isinstance(event, PieceMoved):
            self._append(
                f"{event.color.value} {event.kind.value} "
                f"{_cell_label(event.from_cell, self._board_rows)}-"
                f"{_cell_label(event.to_cell, self._board_rows)}"
            )
        elif isinstance(event, PieceCaptured):
            self._append(
                f"{event.color.value} {event.kind.value} captured "
                f"at {_cell_label(event.cell, self._board_rows)}"
            )
        elif isinstance(event, PiecePromoted):
            self._append(
                f"promoted to {event.to_kind.value} "
                f"at {_cell_label(event.cell, self._board_rows)}"
            )

    def _append(self, text: str) -> None:
        self._entries.append(text)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

    @property
    def entries(self) -> List[str]:
        return list(self._entries)
