from kungfu_chess.model import Color, PieceKind, Position
from ui.events.events import GameOver, PieceCaptured, PieceMoved
from ui.hud.hud_renderer import HudRenderer
from ui.hud.move_log_panel import MoveLogPanel
from ui.hud.player_labels import PlayerLabels
from ui.hud.score_panel import ScorePanel
from ui.tests.support import FakeCanvas


def test_draws_scores_and_move_log_entries_to_the_right_of_the_board():
    canvas = FakeCanvas()
    hud = HudRenderer(canvas, board_pixel_width=800)

    score_panel = ScorePanel()
    score_panel.handle(PieceCaptured("b1", Color.BLACK, PieceKind.QUEEN, Position(0, 0)))
    move_log = MoveLogPanel(board_rows=8)
    move_log.handle(PieceMoved("w1", Color.WHITE, PieceKind.PAWN, Position(6, 0), Position(4, 0)))
    labels = PlayerLabels()

    hud.draw(labels, score_panel, move_log)

    texts = [text for text, x, y in canvas.draw_text_calls]
    assert all(x >= 800 for _, x, _ in canvas.draw_text_calls)
    assert "Score: 9" in texts
    assert "Score: 0" in texts
    assert "white pawn a2-a4" in texts
    assert not any(t.startswith("Winner:") for t in texts)


def test_draws_a_winner_line_once_the_game_is_over():
    canvas = FakeCanvas()
    hud = HudRenderer(canvas, board_pixel_width=800)

    labels = PlayerLabels()
    labels.handle(GameOver(Color.WHITE))

    hud.draw(labels, ScorePanel(), MoveLogPanel(board_rows=8))

    texts = [text for text, x, y in canvas.draw_text_calls]
    assert "Winner: white" in texts
