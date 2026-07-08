import unittest
from io import StringIO
from unittest.mock import patch

from chess_engine import ChessEngine
from types_and_constants import Color, PieceType, Position, Piece


class TestChessEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ChessEngine(cooldown_duration=100)
        self.engine.add_board_row([Piece(Color.WHITE, PieceType.KING), None])
        self.engine.add_board_row([None, Piece(Color.BLACK, PieceType.KING)])
        self.engine.init_cooldown_matrix()

    def test_click_out_of_bounds_is_ignored(self):
        self.engine.handle_click_position(Position(-1, 0))
        self.engine.handle_click_position(Position(5, 5))

        self.assertIsNone(self.engine.selected_pos)
        self.assertEqual(self.engine.board_matrix[0][0].piece_type, PieceType.KING)

    def test_selecting_a_piece_sets_selection(self):
        self.engine.handle_click_position(Position(0, 0))

        self.assertEqual(self.engine.selected_pos, Position(0, 0))

    def test_clicking_an_empty_square_without_selection_does_nothing(self):
        self.engine.handle_click_position(Position(1, 0))

        self.assertIsNone(self.engine.selected_pos)

    def test_valid_move_updates_board_and_clears_selection(self):
        self.engine.handle_click_position(Position(0, 0))
        self.engine.handle_click_position(Position(0, 1))

        self.assertIsNone(self.engine.board_matrix[0][0])
        self.assertEqual(self.engine.board_matrix[0][1].color, Color.WHITE)
        self.assertEqual(self.engine.board_matrix[0][1].piece_type, PieceType.KING)
        self.assertIsNone(self.engine.selected_pos)

    def test_same_color_piece_switches_selection(self):
        self.engine.board_matrix[0][1] = Piece(Color.WHITE, PieceType.PAWN)

        self.engine.handle_click_position(Position(0, 0))
        self.engine.handle_click_position(Position(0, 1))

        self.assertEqual(self.engine.selected_pos, Position(0, 1))

    def test_illegal_move_clears_selection_without_mutating_board(self):
        self.engine.handle_click_position(Position(0, 0))
        self.engine.handle_click_position(Position(1, 1))

        self.assertIsNone(self.engine.selected_pos)
        self.assertIsNone(self.engine.board_matrix[0][0])
        self.assertIsNotNone(self.engine.board_matrix[1][1])

    def test_cooldown_prevents_immediate_repeated_move(self):
        self.engine.handle_click_position(Position(0, 0))
        self.engine.handle_click_position(Position(0, 1))

        self.engine.handle_click_position(Position(0, 1))
        self.engine.handle_click_position(Position(0, 0))

        self.assertIsNone(self.engine.board_matrix[0][0])
        self.assertIsNotNone(self.engine.board_matrix[0][1])

    def test_cooldown_expires_and_move_succeeds(self):
        self.engine.handle_click_position(Position(0, 0))
        self.engine.handle_click_position(Position(0, 1))

        self.engine.advance_time(105)
        self.engine.handle_click_position(Position(0, 1))
        self.engine.handle_click_position(Position(0, 0))

        self.assertIsNotNone(self.engine.board_matrix[0][0])
        self.assertIsNone(self.engine.board_matrix[0][1])

    def test_init_cooldown_matrix_and_print_board_are_supported(self):
        engine = ChessEngine(cooldown_duration=50)
        engine.add_board_row([Piece(Color.WHITE, PieceType.KING), None])
        engine.init_cooldown_matrix()

        self.assertEqual(engine.cooldown_matrix, [[0, 0]])

        with patch("sys.stdout", new=StringIO()) as fake_out:
            engine.print_current_board()

        self.assertEqual(fake_out.getvalue().strip(), "wK .")


if __name__ == "__main__":
    unittest.main()