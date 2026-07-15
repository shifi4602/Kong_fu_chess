from kungfu_chess.model import Color
from ui.events.events import GameOver
from ui.hud.game_over_banner import GameOverBanner
from ui.hud.player_labels import PlayerLabels
from ui.tests.support import FakeCanvas


def test_draws_nothing_before_the_game_is_over():
    canvas = FakeCanvas()
    banner = GameOverBanner(canvas, board_width=800, board_height=800)

    banner.draw(PlayerLabels())

    assert canvas.blit_calls == []
    assert canvas.draw_text_calls == []


def test_draws_the_dim_overlay_and_centered_winner_text():
    canvas = FakeCanvas()
    banner = GameOverBanner(canvas, board_width=800, board_height=800)
    labels = PlayerLabels()
    labels.handle(GameOver(Color.WHITE))

    banner.draw(labels)

    assert len(canvas.blit_calls) == 1  # the dim overlay
    texts = [text for text, x, y in canvas.draw_text_calls]
    assert texts == ["WHITE WINS"]
