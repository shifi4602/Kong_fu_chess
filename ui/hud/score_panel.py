"""Tracks captured-material score per color. This is a presentational
convention (standard chess point values used only for display), not a
rule -- it never influences legality, turns, or outcome; it only tallies
events the engine has already resolved.
"""
from __future__ import annotations

from typing import Dict

from kungfu_chess.model import Color, PieceKind
from ui.events.events import Event, PieceCaptured

_POINT_VALUES: Dict[PieceKind, int] = {
    PieceKind.PAWN: 1,
    PieceKind.KNIGHT: 3,
    PieceKind.BISHOP: 3,
    PieceKind.ROOK: 5,
    PieceKind.QUEEN: 9,
    PieceKind.KING: 0,
}


class ScorePanel:
    def __init__(self) -> None:
        self._score: Dict[Color, int] = {Color.WHITE: 0, Color.BLACK: 0}

    def handle(self, event: Event) -> None:
        if not isinstance(event, PieceCaptured):
            return
        capturing_color = Color.BLACK if event.color == Color.WHITE else Color.WHITE
        self._score[capturing_color] += _POINT_VALUES[event.kind]

    def score(self, color: Color) -> int:
        return self._score[color]
