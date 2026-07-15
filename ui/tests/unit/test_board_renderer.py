from ui.rendering.board_renderer import BoardRenderer
from ui.tests.support import FakeCanvas, FakeImage


def test_draw_draws_background_then_every_placement():
    canvas = FakeCanvas()
    background = FakeImage(path=None, size=(800, 800))
    renderer = BoardRenderer(canvas, background)

    sprite = FakeImage(path=None, size=(100, 100))
    placements = [(sprite, 0, 0), (sprite, 700, 700)]

    renderer.draw(placements)

    assert canvas.begin_frame_calls == [background]
    assert canvas.present_count == 0
    assert canvas.blit_calls == [(sprite, 0, 0), (sprite, 700, 700)]


def test_render_also_presents():
    canvas = FakeCanvas()
    background = FakeImage(path=None, size=(800, 800))
    renderer = BoardRenderer(canvas, background)

    renderer.render([])

    assert canvas.present_count == 1
