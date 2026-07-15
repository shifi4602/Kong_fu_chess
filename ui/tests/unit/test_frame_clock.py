import pytest

from ui.animation.frame_clock import FrameClock


def test_frame_duration_is_the_inverse_of_target_fps():
    clock = FrameClock(target_fps=60)
    assert clock.frame_duration == 1.0 / 60


def test_tick_returns_delta_since_the_previous_tick():
    clock = FrameClock(target_fps=60)
    assert clock.tick(now=0.0) == 0.0  # first call has no prior tick
    assert clock.tick(now=0.1) == pytest.approx(0.1)
    assert clock.tick(now=0.35) == pytest.approx(0.25)


def test_measured_fps_updates_once_a_window_of_at_least_one_second_elapses():
    clock = FrameClock(target_fps=60)
    for i in range(60):
        clock.tick(now=i * (1.0 / 60))
    assert clock.measured_fps == 0.0  # window hasn't reached 1s yet

    clock.tick(now=1.0)
    assert clock.measured_fps == 61.0  # 61 ticks over exactly 1.0s
