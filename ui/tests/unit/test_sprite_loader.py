from ui.assets.sprite_loader import SpriteLoader
from ui.tests.support import FakeCanvas


def test_loads_config_and_all_frames_for_a_real_state():
    canvas = FakeCanvas()
    loader = SpriteLoader(canvas, cell_size=100)

    result = loader.load("wK", "idle")

    assert result.config.frames_per_sec == 4
    assert result.config.is_loop is True
    assert result.config.next_state_when_finished == "idle"
    assert len(result.frames) == 5


def test_caches_repeated_loads_of_the_same_state():
    canvas = FakeCanvas()
    loader = SpriteLoader(canvas, cell_size=100)

    first = loader.load("wP", "move")
    second = loader.load("wP", "move")

    assert first is second
    assert len(canvas.load_image_calls) == 5
