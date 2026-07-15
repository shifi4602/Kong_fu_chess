from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Position
from ui.rendering.coordinate_mapper import CoordinateMapper


def _mapper(cell_size: int = 100) -> CoordinateMapper:
    return CoordinateMapper(BoardMapper(cell_size=cell_size, rows=8, cols=8), cell_size)


def test_cell_top_left_matches_board_mapper():
    mapper = _mapper()
    assert mapper.cell_top_left(Position(row=2, col=3)) == (300, 200)


def test_sprite_anchor_is_top_left_for_a_sprite_that_fills_the_cell():
    mapper = _mapper(cell_size=100)
    assert mapper.sprite_anchor(Position(row=0, col=0), sprite_size=(100, 100)) == (0, 0)


def test_sprite_anchor_centers_horizontally_and_aligns_to_the_bottom():
    mapper = _mapper(cell_size=100)
    # cell top-left is (100, 100); a 60x80 sprite gets a 20px horizontal
    # margin on each side and sits flush against the cell's bottom edge.
    assert mapper.sprite_anchor(Position(row=1, col=1), sprite_size=(60, 80)) == (120, 120)


def test_anchor_at_applies_the_same_offset_to_an_arbitrary_pixel():
    mapper = _mapper(cell_size=100)
    # Same math as sprite_anchor, but starting from a raw (interpolated)
    # pixel instead of a cell's own top-left.
    assert mapper.anchor_at((150.0, 100.0), sprite_size=(60, 80)) == (170, 120)


def test_anchor_at_rounds_fractional_pixels():
    mapper = _mapper(cell_size=100)
    assert mapper.anchor_at((150.4, 100.6), sprite_size=(100, 100)) == (150, 101)
