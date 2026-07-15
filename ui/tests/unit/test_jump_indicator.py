from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Position
from ui.rendering.coordinate_mapper import CoordinateMapper
from ui.rendering.jump_indicator import JumpIndicator
from ui.tests.support import FakeCanvas


def test_draws_nothing_with_no_jumping_pieces():
    canvas = FakeCanvas()
    mapper = CoordinateMapper(BoardMapper(cell_size=100, rows=8, cols=8), cell_size=100)
    indicator = JumpIndicator(canvas, mapper, cell_size=100)

    indicator.draw([])

    assert canvas.blit_calls == []


def test_draws_an_overlay_for_each_jumping_cell():
    canvas = FakeCanvas()
    mapper = CoordinateMapper(BoardMapper(cell_size=100, rows=8, cols=8), cell_size=100)
    indicator = JumpIndicator(canvas, mapper, cell_size=100)

    indicator.draw([Position(0, 0), Position(3, 3)])

    assert len(canvas.blit_calls) == 2
    positions = {(x, y) for _, x, y in canvas.blit_calls}
    assert positions == {(0, 0), (300, 300)}
