from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Position


def test_pixel_to_position_origin():
    mapper = BoardMapper(cell_size=80)
    assert mapper.pixel_to_position(0, 0) == Position(0, 0)


def test_pixel_to_position_second_col():
    mapper = BoardMapper(cell_size=80)
    assert mapper.pixel_to_position(80, 0) == Position(0, 1)


def test_pixel_to_position_second_row():
    mapper = BoardMapper(cell_size=80)
    assert mapper.pixel_to_position(0, 80) == Position(1, 0)


def test_pixel_to_position_last_cell():
    mapper = BoardMapper(cell_size=80, rows=8, cols=8)
    assert mapper.pixel_to_position(559, 559) == Position(6, 6)


def test_pixel_to_position_negative_x():
    mapper = BoardMapper(cell_size=80)
    assert mapper.pixel_to_position(-1, 0) is None


def test_pixel_to_position_negative_y():
    mapper = BoardMapper(cell_size=80)
    assert mapper.pixel_to_position(0, -1) is None


def test_pixel_to_position_past_cols():
    mapper = BoardMapper(cell_size=80, rows=8, cols=8)
    assert mapper.pixel_to_position(640, 0) is None


def test_pixel_to_position_past_rows():
    mapper = BoardMapper(cell_size=80, rows=8, cols=8)
    assert mapper.pixel_to_position(0, 640) is None


def test_position_to_pixel_origin():
    mapper = BoardMapper(cell_size=80)
    assert mapper.position_to_pixel(Position(0, 0)) == (0, 0)


def test_position_to_pixel_col_maps_to_x():
    mapper = BoardMapper(cell_size=80)
    x, y = mapper.position_to_pixel(Position(0, 3))
    assert x == 240
    assert y == 0


def test_position_to_pixel_row_maps_to_y():
    mapper = BoardMapper(cell_size=80)
    x, y = mapper.position_to_pixel(Position(2, 0))
    assert x == 0
    assert y == 160


def test_position_to_pixel_general():
    mapper = BoardMapper(cell_size=100)
    assert mapper.position_to_pixel(Position(2, 3)) == (300, 200)
