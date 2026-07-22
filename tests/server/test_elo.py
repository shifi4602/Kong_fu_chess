from kungfu_chess.model import Color
from server.persistence.elo import compute_new_ratings


def test_equal_ratings_white_wins_nets_plus_16_minus_16_at_k32():
    white_after, black_after = compute_new_ratings(1200, 1200, Color.WHITE, k_factor=32)
    assert white_after == 1216
    assert black_after == 1184


def test_equal_ratings_black_wins_nets_plus_16_minus_16_at_k32():
    white_after, black_after = compute_new_ratings(1200, 1200, Color.BLACK, k_factor=32)
    assert white_after == 1184
    assert black_after == 1216


def test_underdog_win_nets_more_than_an_even_matchup():
    white_after, _ = compute_new_ratings(1000, 1400, Color.WHITE, k_factor=32)
    assert white_after - 1000 > 16


def test_favorite_win_nets_less_than_an_even_matchup():
    white_after, _ = compute_new_ratings(1400, 1000, Color.WHITE, k_factor=32)
    assert white_after - 1400 < 16


def test_ratings_never_go_negative_for_a_lopsided_loss():
    _, black_after = compute_new_ratings(2400, 100, Color.WHITE, k_factor=32)
    assert black_after >= 0


def test_k_factor_scales_the_swing():
    white_after_16, _ = compute_new_ratings(1200, 1200, Color.WHITE, k_factor=16)
    white_after_32, _ = compute_new_ratings(1200, 1200, Color.WHITE, k_factor=32)
    assert (white_after_16 - 1200) * 2 == white_after_32 - 1200
