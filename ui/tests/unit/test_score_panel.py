from kungfu_chess.model import Color, PieceKind, Position
from ui.events.events import GameOver, PieceCaptured
from ui.hud.score_panel import ScorePanel


def test_starts_at_zero_for_both_colors():
    panel = ScorePanel()
    assert panel.score(Color.WHITE) == 0
    assert panel.score(Color.BLACK) == 0


def test_a_captured_black_piece_credits_white_with_its_point_value():
    panel = ScorePanel()
    panel.handle(PieceCaptured("b1", Color.BLACK, PieceKind.QUEEN, Position(0, 0)))

    assert panel.score(Color.WHITE) == 9
    assert panel.score(Color.BLACK) == 0


def test_a_captured_white_piece_credits_black_with_its_point_value():
    panel = ScorePanel()
    panel.handle(PieceCaptured("w1", Color.WHITE, PieceKind.ROOK, Position(0, 0)))

    assert panel.score(Color.BLACK) == 5
    assert panel.score(Color.WHITE) == 0


def test_captures_accumulate():
    panel = ScorePanel()
    panel.handle(PieceCaptured("b1", Color.BLACK, PieceKind.PAWN, Position(0, 0)))
    panel.handle(PieceCaptured("b2", Color.BLACK, PieceKind.KNIGHT, Position(0, 1)))

    assert panel.score(Color.WHITE) == 1 + 3


def test_ignores_events_that_are_not_captures():
    panel = ScorePanel()
    panel.handle(PieceCaptured("b1", Color.BLACK, PieceKind.PAWN, Position(0, 0)))
    panel.handle(GameOver(Color.WHITE))

    assert panel.score(Color.WHITE) == 1
