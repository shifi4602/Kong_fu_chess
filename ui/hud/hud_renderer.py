"""Draws the sidebar: player labels + live score + move log. Purely
mechanical -- it only reads already-computed state off the three panels
and calls Canvas.draw_text; no event handling happens here.
"""
from __future__ import annotations

from kungfu_chess.model import Color
from ui.rendering.canvas import Canvas

from .move_log_panel import MoveLogPanel
from .player_labels import PlayerLabels
from .score_panel import ScorePanel

SIDEBAR_WIDTH = 300

_LINE_HEIGHT = 20
_WHITE_TEXT = (255, 255, 255, 255)
_GOLD_TEXT = (0, 215, 255, 255)


class HudRenderer:
    def __init__(self, canvas: Canvas, board_pixel_width: int) -> None:
        self._canvas = canvas
        # magic number 16 is the padding between the board and the sidebar
        self._x = board_pixel_width + 16

    def draw(self, player_labels: PlayerLabels, score_panel: ScorePanel, move_log: MoveLogPanel) -> None:
        # 30 is the padding between the top of the canvas and the first line of text
        y = 30
        self._canvas.draw_text("White", self._x, y, font_size=0.7, color=_WHITE_TEXT)
        y += _LINE_HEIGHT
        self._canvas.draw_text(f"Score: {score_panel.score(Color.WHITE)}", self._x, y, font_size=0.55)
        y += _LINE_HEIGHT * 2

        self._canvas.draw_text("Black", self._x, y, font_size=0.7, color=_WHITE_TEXT)
        y += _LINE_HEIGHT
        self._canvas.draw_text(f"Score: {score_panel.score(Color.BLACK)}", self._x, y, font_size=0.55)
        y += _LINE_HEIGHT * 2

        if player_labels.winner is not None:
            self._canvas.draw_text(
                f"Winner: {player_labels.winner.value}", self._x, y, font_size=0.6, color=_GOLD_TEXT
            )
            y += _LINE_HEIGHT * 2

        # 15 is the padding between the winner text and the move log
        self._canvas.draw_text("Moves:", self._x, y, font_size=0.6, color=_WHITE_TEXT)
        y += _LINE_HEIGHT
        for entry in move_log.entries[-15:]:
            self._canvas.draw_text(entry, self._x, y, font_size=0.45)
            y += _LINE_HEIGHT
