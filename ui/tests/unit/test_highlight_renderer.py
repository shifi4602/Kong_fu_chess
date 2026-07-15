from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Position
from ui.rendering.coordinate_mapper import CoordinateMapper
from ui.rendering.highlight_renderer import HighlightRenderer
from ui.tests.support import FakeCanvas


def test_draws_nothing_when_no_cell_is_selected():
    canvas = FakeCanvas()
    mapper = CoordinateMapper(BoardMapper(cell_size=100, rows=8, cols=8), cell_size=100)
    highlight = HighlightRenderer(canvas, mapper, cell_size=100)

    highlight.draw(None)

    assert canvas.blit_calls == []


def test_draws_the_translucent_overlay_at_the_selected_cell():
    canvas = FakeCanvas()
    mapper = CoordinateMapper(BoardMapper(cell_size=100, rows=8, cols=8), cell_size=100)
    highlight = HighlightRenderer(canvas, mapper, cell_size=100)

    highlight.draw(Position(row=2, col=3))

    assert len(canvas.blit_calls) == 1
    image, x, y = canvas.blit_calls[0]
    assert (x, y) == (300, 200)
