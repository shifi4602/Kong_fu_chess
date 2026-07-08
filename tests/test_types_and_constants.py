import pytest
from types_and_constants import Color, PieceType, Position, Piece

# --- Your original tests ---

def test_color_from_value_parses_known_values():
    assert Color.from_value("w") == Color.WHITE
    assert Color.from_value("b") == Color.BLACK

def test_color_from_value_rejects_unknown_values():
    with pytest.raises(ValueError):
        Color.from_value("x")

def test_piece_type_from_value_parses_all_supported_values():
    assert PieceType.from_value("K") == PieceType.KING
    assert PieceType.from_value("Q") == PieceType.QUEEN
    assert PieceType.from_value("R") == PieceType.ROOK
    assert PieceType.from_value("B") == PieceType.BISHOP
    assert PieceType.from_value("N") == PieceType.KNIGHT
    assert PieceType.from_value("P") == PieceType.PAWN

def test_piece_type_from_value_rejects_unknown_values():
    with pytest.raises(ValueError):
        PieceType.from_value("Z")

def test_position_and_piece_are_immutable():
    position = Position(row=3, col=5)
    piece = Piece(color=Color.WHITE, piece_type=PieceType.PAWN)

    assert position.row == 3
    assert position.col == 5
    assert piece.color == Color.WHITE
    assert piece.piece_type == PieceType.PAWN

    with pytest.raises(AttributeError):
        position.row = 4

    with pytest.raises(AttributeError):
        piece.color = Color.BLACK

def test_position_and_piece_support_value_equality():
    assert Position(1, 2) == Position(1, 2)
    assert Piece(Color.WHITE, PieceType.PAWN) == Piece(Color.WHITE, PieceType.PAWN)