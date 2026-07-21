from server.session.manual_clock import ManualClock


def test_defaults_to_zero():
    clock = ManualClock()
    assert clock.now() == 0.0


def test_set_converts_ms_to_seconds():
    clock = ManualClock()
    clock.set(1500)
    assert clock.now() == 1.5


def test_initial_ms_is_respected():
    clock = ManualClock(initial_ms=2000)
    assert clock.now() == 2.0
