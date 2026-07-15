from ui.animation.anim_clock import AnimClock


def test_looping_clock_wraps_the_frame_index_and_never_finishes():
    clock = AnimClock(frames_per_sec=4, is_loop=True)
    assert clock.frame_index(elapsed=0.0, frame_count=5) == 0
    assert clock.frame_index(elapsed=0.26, frame_count=5) == 1
    assert clock.frame_index(elapsed=1.3, frame_count=5) == 0  # wrapped: 5 frames in
    assert clock.is_finished(elapsed=1000.0, frame_count=5) is False


def test_non_looping_clock_clamps_to_the_last_frame_and_reports_finished():
    clock = AnimClock(frames_per_sec=10, is_loop=False)
    assert clock.frame_index(elapsed=0.0, frame_count=5) == 0
    assert clock.frame_index(elapsed=0.35, frame_count=5) == 3
    assert clock.frame_index(elapsed=10.0, frame_count=5) == 4  # clamped
    assert clock.is_finished(elapsed=0.49, frame_count=5) is False
    assert clock.is_finished(elapsed=0.5, frame_count=5) is True
