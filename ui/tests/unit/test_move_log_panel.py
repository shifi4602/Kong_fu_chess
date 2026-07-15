from kungfu_chess.model import Color, PieceKind, Position
from ui.events.events import GameOver, PieceCaptured, PieceMoved, PiecePromoted
from ui.hud.move_log_panel import MoveLogPanel


def test_a_move_is_logged_with_algebraic_style_cell_labels():
    panel = MoveLogPanel(board_rows=8)
    panel.handle(PieceMoved("w1", Color.WHITE, PieceKind.PAWN, Position(6, 0), Position(4, 0)))

    assert panel.entries == ["white pawn a2-a4"]


def test_a_capture_is_logged():
    panel = MoveLogPanel(board_rows=8)
    panel.handle(PieceCaptured("b1", Color.BLACK, PieceKind.KNIGHT, Position(3, 3)))

    assert panel.entries == ["black knight captured at d5"]


def test_a_promotion_is_logged():
    panel = MoveLogPanel(board_rows=8)
    panel.handle(PiecePromoted("w1", PieceKind.PAWN, PieceKind.QUEEN, Position(0, 0)))

    assert panel.entries == ["promoted to queen at a8"]


def test_game_over_is_not_logged_as_a_move():
    panel = MoveLogPanel(board_rows=8)
    panel.handle(GameOver(Color.WHITE))

    assert panel.entries == []


def test_entries_are_capped_at_max_entries():
    panel = MoveLogPanel(board_rows=8, max_entries=3)
    for i in range(5):
        panel.handle(PieceMoved("w1", Color.WHITE, PieceKind.PAWN, Position(6, 0), Position(6 - i, 0)))

    assert len(panel.entries) == 3
