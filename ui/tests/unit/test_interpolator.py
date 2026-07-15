from ui.animation.interpolator import lerp_point


def test_progress_zero_is_src():
    assert lerp_point((0, 0), (100, 200), progress=0.0) == (0, 0)


def test_progress_one_is_dst():
    assert lerp_point((0, 0), (100, 200), progress=1.0) == (100, 200)


def test_progress_midway_is_the_midpoint():
    assert lerp_point((0, 0), (100, 200), progress=0.5) == (50.0, 100.0)


def test_works_for_negative_direction_travel():
    assert lerp_point((300, 0), (0, 0), progress=0.25) == (225.0, 0.0)
