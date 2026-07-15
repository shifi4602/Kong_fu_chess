from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Position
from ui.rendering.capture_flash import CaptureFlash
from ui.rendering.coordinate_mapper import CoordinateMapper
from ui.tests.support import FakeCanvas


def _flash(duration: float = 0.4) -> CaptureFlash:
    canvas = FakeCanvas()
    mapper = CoordinateMapper(BoardMapper(cell_size=100, rows=8, cols=8), cell_size=100)
    return CaptureFlash(canvas, mapper, cell_size=100, duration=duration), canvas


def test_draws_nothing_with_no_recorded_capture():
    flash, canvas = _flash()
    flash.draw(now=0.0)
    assert canvas.blit_calls == []


def test_draws_an_overlay_right_after_a_capture_is_recorded():
    flash, canvas = _flash()
    flash.record(Position(2, 3), now=1.0)

    flash.draw(now=1.0)

    assert len(canvas.blit_calls) == 1
    _, x, y = canvas.blit_calls[0]
    assert (x, y) == (300, 200)


def test_stops_drawing_once_the_duration_elapses():
    flash, canvas = _flash(duration=0.4)
    flash.record(Position(0, 0), now=1.0)

    flash.draw(now=1.39)
    assert len(canvas.blit_calls) == 1

    canvas.blit_calls.clear()
    flash.draw(now=1.5)  # clearly past the 0.4s duration
    assert canvas.blit_calls == []


def test_multiple_captures_are_tracked_independently():
    flash, canvas = _flash(duration=0.4)
    flash.record(Position(0, 0), now=0.0)
    flash.record(Position(1, 1), now=0.2)

    flash.draw(now=0.3)  # first still active (0.3s in), second still active (0.1s in)
    assert len(canvas.blit_calls) == 2
