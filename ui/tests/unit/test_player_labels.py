from kungfu_chess.model import Color, PieceKind, Position
from ui.events.events import GameOver, PieceCaptured
from ui.hud.player_labels import PlayerLabels


def test_no_winner_before_a_game_over_event():
    labels = PlayerLabels()
    assert labels.winner is None


def test_records_the_winner_from_a_game_over_event():
    labels = PlayerLabels()
    labels.handle(GameOver(Color.BLACK))

    assert labels.winner == Color.BLACK


def test_ignores_other_events():
    labels = PlayerLabels()
    labels.handle(PieceCaptured("w1", Color.WHITE, PieceKind.PAWN, Position(0, 0)))

    assert labels.winner is None
