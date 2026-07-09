import kungfu_chess.config as config


def test_cell_size_positive():
    assert config.CELL_SIZE > 0


def test_travel_duration_positive():
    assert config.TRAVEL_DURATION > 0


def test_board_rows():
    assert config.BOARD_ROWS == 8


def test_board_cols():
    assert config.BOARD_COLS == 8


def test_fps_positive():
    assert config.FPS > 0
