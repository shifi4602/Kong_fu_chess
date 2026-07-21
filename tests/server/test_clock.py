from server.clock import FakeWallClock, SystemWallClock


def test_fake_wall_clock_starts_at_initial_ms():
    clock = FakeWallClock(initial_ms=500)
    assert clock.now_ms() == 500


def test_fake_wall_clock_advance():
    clock = FakeWallClock()
    clock.advance(100)
    clock.advance(50)
    assert clock.now_ms() == 150


def test_fake_wall_clock_set():
    clock = FakeWallClock()
    clock.set(999)
    assert clock.now_ms() == 999


def test_system_wall_clock_returns_increasing_ints():
    clock = SystemWallClock()
    first = clock.now_ms()
    second = clock.now_ms()
    assert isinstance(first, int)
    assert second >= first
