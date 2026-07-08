import unittest

from types_and_constants import Color, PieceType, Position, Piece


class TestTypesAndConstants(unittest.TestCase):
    def test_color_from_value_parses_known_values(self):
        self.assertEqual(Color.from_value("w"), Color.WHITE)
        self.assertEqual(Color.from_value("b"), Color.BLACK)

    def test_color_from_value_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            Color.from_value("x")

    def test_piece_type_from_value_parses_all_supported_values(self):
        self.assertEqual(PieceType.from_value("K"), PieceType.KING)
        self.assertEqual(PieceType.from_value("Q"), PieceType.QUEEN)
        self.assertEqual(PieceType.from_value("R"), PieceType.ROOK)
        self.assertEqual(PieceType.from_value("B"), PieceType.BISHOP)
        self.assertEqual(PieceType.from_value("N"), PieceType.KNIGHT)
        self.assertEqual(PieceType.from_value("P"), PieceType.PAWN)

    def test_piece_type_from_value_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            PieceType.from_value("Z")

    def test_position_and_piece_are_immutable(self):
        position = Position(row=3, col=5)
        piece = Piece(color=Color.WHITE, piece_type=PieceType.PAWN)

        self.assertEqual(position.row, 3)
        self.assertEqual(position.col, 5)
        self.assertEqual(piece.color, Color.WHITE)
        self.assertEqual(piece.piece_type, PieceType.PAWN)

        with self.assertRaises(Exception):
            position.row = 4

        with self.assertRaises(Exception):
            piece.color = Color.BLACK

    def test_position_and_piece_support_value_equality(self):
        self.assertEqual(Position(1, 2), Position(1, 2))
        self.assertEqual(Piece(Color.WHITE, PieceType.PAWN), Piece(Color.WHITE, PieceType.PAWN))


if __name__ == "__main__":
    unittest.main()