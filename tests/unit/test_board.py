import pytest
from kungfu_chess.model import Board, Color, Piece, PieceKind, Position


def _piece(color=Color.WHITE, kind=PieceKind.KING) -> Piece:
    return Piece(id='t', color=color, kind=kind, cell=Position(0, 0))


def test_place_and_get():
    board = Board(4, 4)
    piece = _piece()
    board.place(piece, Position(1, 2))
    assert board.get(Position(1, 2)) is piece


def test_place_sets_piece_cell():
    board = Board(4, 4)
    piece = _piece()
    board.place(piece, Position(2, 3))
    assert piece.cell == Position(2, 3)


def test_get_empty_returns_none():
    board = Board(4, 4)
    assert board.get(Position(0, 0)) is None


def test_remove_returns_piece():
    board = Board(4, 4)
    piece = _piece()
    board.place(piece, Position(0, 0))
    removed = board.remove(Position(0, 0))
    assert removed is piece


def test_remove_clears_cell():
    board = Board(4, 4)
    board.place(_piece(), Position(0, 0))
    board.remove(Position(0, 0))
    assert board.get(Position(0, 0)) is None


def test_remove_empty_returns_none():
    board = Board(4, 4)
    assert board.remove(Position(0, 0)) is None


def test_in_bounds_corners():
    board = Board(4, 4)
    assert board.in_bounds(Position(0, 0))
    assert board.in_bounds(Position(3, 3))


def test_in_bounds_negative():
    board = Board(4, 4)
    assert not board.in_bounds(Position(-1, 0))
    assert not board.in_bounds(Position(0, -1))


def test_in_bounds_past_edge():
    board = Board(4, 4)
    assert not board.in_bounds(Position(4, 0))
    assert not board.in_bounds(Position(0, 4))


def test_is_occupied_empty():
    board = Board(4, 4)
    assert not board.is_occupied(Position(0, 0))


def test_is_occupied_after_place():
    board = Board(4, 4)
    board.place(_piece(), Position(0, 0))
    assert board.is_occupied(Position(0, 0))


def test_is_occupied_after_remove():
    board = Board(4, 4)
    board.place(_piece(), Position(0, 0))
    board.remove(Position(0, 0))
    assert not board.is_occupied(Position(0, 0))


def test_all_pieces():
    board = Board(4, 4)
    p1 = _piece(Color.WHITE, PieceKind.KING)
    p2 = _piece(Color.BLACK, PieceKind.ROOK)
    board.place(p1, Position(0, 0))
    board.place(p2, Position(1, 1))
    pieces = board.all_pieces()
    assert p1 in pieces
    assert p2 in pieces
    assert len(pieces) == 2


def test_pieces_by_color_white():
    board = Board(4, 4)
    wp = _piece(Color.WHITE, PieceKind.KING)
    bp = _piece(Color.BLACK, PieceKind.ROOK)
    board.place(wp, Position(0, 0))
    board.place(bp, Position(1, 1))
    whites = board.pieces_by_color(Color.WHITE)
    assert wp in whites
    assert bp not in whites


def test_pieces_by_color_empty():
    board = Board(4, 4)
    board.place(_piece(Color.WHITE), Position(0, 0))
    assert board.pieces_by_color(Color.BLACK) == []


def test_place_out_of_bounds_raises():
    board = Board(4, 4)
    with pytest.raises(ValueError):
        board.place(_piece(), Position(10, 10))


def test_iter_yields_all_position_piece_pairs():
    board = Board(4, 4)
    p1 = _piece(Color.WHITE, PieceKind.KING)
    p2 = _piece(Color.BLACK, PieceKind.ROOK)
    board.place(p1, Position(0, 0))
    board.place(p2, Position(1, 1))
    pairs = list(board)
    assert (Position(0, 0), p1) in pairs
    assert (Position(1, 1), p2) in pairs
    assert len(pairs) == 2


def test_repr_includes_dimensions_and_count():
    board = Board(4, 4)
    board.place(_piece(), Position(0, 0))
    r = repr(board)
    assert '4x4' in r
    assert '1' in r
