from __future__ import annotations

from typing import Tuple

from kungfu_chess.model import Color


def compute_new_ratings(
    white_rating: int, black_rating: int, winner_color: Color, k_factor: int = 32
) -> Tuple[int, int]:
    """Standard ELO update, fixed K-factor. Pure function, no I/O — unit
    tested in complete isolation from the database, the bus, or sessions.
    """
    expected_white = 1.0 / (1.0 + 10.0 ** ((black_rating - white_rating) / 400.0))
    expected_black = 1.0 - expected_white

    score_white = 1.0 if winner_color == Color.WHITE else 0.0
    score_black = 1.0 - score_white

    white_after = round(white_rating + k_factor * (score_white - expected_white))
    black_after = round(black_rating + k_factor * (score_black - expected_black))
    return white_after, black_after
