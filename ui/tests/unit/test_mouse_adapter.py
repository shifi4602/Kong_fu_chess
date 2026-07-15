from typing import Tuple

from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper, Controller
from kungfu_chess.io import BoardParser
from kungfu_chess.model import GameState, PieceState, Position
from kungfu_chess.realtime import RealTimeArbiter
from kungfu_chess.rules import default_rule_engine
from ui.input.mouse_adapter import MouseAdapter
from ui.rendering.canvas import MouseButton, MouseEvent


class _FakeClock:
    def now(self) -> float:
        return 0.0


def _wiring() -> Tuple[GameEngine, Controller]:
    board = BoardParser().parse("wP .\n.  bP")
    state = GameState(board=board)
    arbiter = RealTimeArbiter(_FakeClock(), travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    mapper = BoardMapper(cell_size=100, rows=2, cols=2)
    return engine, Controller(engine, mapper)


def test_left_click_selects_then_deselects_a_piece():
    _, controller = _wiring()
    adapter = MouseAdapter(controller)

    adapter.handle([MouseEvent(MouseButton.LEFT, x=10, y=10)])
    assert controller.selected == Position(row=0, col=0)

    adapter.handle([MouseEvent(MouseButton.LEFT, x=10, y=10)])
    assert controller.selected is None


def test_right_click_starts_a_jump():
    engine, controller = _wiring()
    adapter = MouseAdapter(controller)

    adapter.handle([MouseEvent(MouseButton.RIGHT, x=10, y=10)])

    piece = engine.get_snapshot().board.get(Position(row=0, col=0))
    assert piece.state == PieceState.JUMPING


def test_ignores_clicks_outside_the_board():
    _, controller = _wiring()
    adapter = MouseAdapter(controller)

    adapter.handle([MouseEvent(MouseButton.LEFT, x=-5, y=-5)])

    assert controller.selected is None
