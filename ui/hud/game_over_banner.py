"""A full-board dimming overlay + centered "<COLOR> WINS" text once the
game is over. Purely reactive to `PlayerLabels.winner` -- decides nothing
about when the game ends.
"""
from __future__ import annotations

from ui.rendering.canvas import Canvas

from .player_labels import PlayerLabels

_DIM_COLOR = (0, 0, 0)
_DIM_ALPHA = 160
_TEXT_COLOR = (0, 215, 255, 255)
_FONT_SIZE = 1.4
_THICKNESS = 3


class GameOverBanner:
    def __init__(self, canvas: Canvas, board_width: int, board_height: int) -> None:
        self._canvas = canvas
        self._board_width = board_width
        self._board_height = board_height
        self._overlay = canvas.blank_image(board_width, board_height, color=_DIM_COLOR, alpha=_DIM_ALPHA)

    def draw(self, player_labels: PlayerLabels) -> None:
        winner = player_labels.winner
        if winner is None:
            return

        self._canvas.blit(self._overlay, 0, 0)

        text = f"{winner.value.upper()} WINS"
        text_w, text_h = self._canvas.text_size(text, font_size=_FONT_SIZE, thickness=_THICKNESS)
        x = (self._board_width - text_w) // 2
        y = (self._board_height + text_h) // 2
        self._canvas.draw_text(text, x, y, font_size=_FONT_SIZE, color=_TEXT_COLOR, thickness=_THICKNESS)
