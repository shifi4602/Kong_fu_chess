import pytest
from kungfu_chess.io import BoardParser
from kungfu_chess.model import Color, PieceKind, Position


def test_parse_places_pieces_at_correct_positions():
    parser = BoardParser()
    board = parser.parse("wK .\n. bK")
    wk = board.get(Position(0, 0))
    bk = board.get(Position(1, 1))
    assert wk is not None
    assert wk.color == Color.WHITE
    assert wk.kind == PieceKind.KING
    assert bk is not None
    assert bk.color == Color.BLACK
    assert bk.kind == PieceKind.KING


def test_parse_empty_cells_are_none():
    parser = BoardParser()
    board = parser.parse("wK .\n. bK")
    assert board.get(Position(0, 1)) is None
    assert board.get(Position(1, 0)) is None


def test_parse_sets_piece_cell():
    parser = BoardParser()
    board = parser.parse("wR .\n. bK")
    piece = board.get(Position(0, 0))
    assert piece.cell == Position(0, 0)


def test_parse_board_dimensions():
    parser = BoardParser()
    board = parser.parse("wK . .\n. . .\n. . bK")
    assert board.rows == 3
    assert board.cols == 3


def test_parse_empty_text_raises():
    parser = BoardParser()
    with pytest.raises(ValueError):
        parser.parse("")


def test_parse_blank_lines_only_raises():
    parser = BoardParser()
    with pytest.raises(ValueError):
        parser.parse("\n\n   \n")


def test_parse_invalid_color_char_raises():
    parser = BoardParser()
    with pytest.raises(ValueError):
        parser.parse("xK .\n. bK")


def test_parse_invalid_kind_char_raises():
    parser = BoardParser()
    with pytest.raises(ValueError):
        parser.parse("wZ .\n. bK")


def test_parse_all_piece_kinds():
    parser = BoardParser()
    board = parser.parse("wK wQ wR wB wN wP")
    assert board.get(Position(0, 0)).kind == PieceKind.KING
    assert board.get(Position(0, 1)).kind == PieceKind.QUEEN
    assert board.get(Position(0, 2)).kind == PieceKind.ROOK
    assert board.get(Position(0, 3)).kind == PieceKind.BISHOP
    assert board.get(Position(0, 4)).kind == PieceKind.KNIGHT
    assert board.get(Position(0, 5)).kind == PieceKind.PAWN


def test_parse_ignores_leading_trailing_blank_lines():
    parser = BoardParser()
    board = parser.parse("\nwK .\n. bK\n")
    assert board.get(Position(0, 0)) is not None
    assert board.rows == 2


def test_parse_jagged_rows_raises():
    parser = BoardParser()
    with pytest.raises(ValueError):
        parser.parse("wK . .\n. bK")


def test_parse_wrong_token_length_raises():
    parser = BoardParser()
    with pytest.raises(ValueError):
        parser.parse("wKK .\n. bK")
