import unittest
from io import StringIO
from unittest.mock import patch

from board_parser import ChessBoard, BoardValidationError

class TestChessBoardParser(unittest.TestCase):

    def test_happy_path_standard_board(self):
        """בדיקת לוח סטנדרטי תקין בגודל 8x8"""
        input_data = (
            "Board:\n"
            "bR bN bB bQ bK bB bN bR\n"
            "bP bP bP bP bP bP bP bP\n"
            ". . . . . . . .\n"
            ". . . . . . . .\n"
            ". . . . . . . .\n"
            ". . . . . . . .\n"
            "wP wP wP wP wP wP wP wP\n"
            "wR wN wB wQ wK wB wN wR"
        )
        # המחרוזת הצפויה כפלט מהלוח (ללא כותרת ה-Board:)
        expected_canonical = "\n".join(input_data.splitlines()[1:])
        
        board = ChessBoard()
        with patch('sys.stdin', StringIO(input_data)):
            board.load_from_stdin()
            
        self.assertEqual(board.width, 8)
        self.assertEqual(board.height, 8)
        self.assertEqual(board.to_canonical_string(), expected_canonical)

    def test_happy_path_rectangular_board(self):
        """בדיקת לוח מלבני תקין (לא ריבועי)"""
        input_data = (
            "Board:\n"
            "wK . . .\n"
            "bP . . .\n"
            ". . . ."
        )
        board = ChessBoard()
        with patch('sys.stdin', StringIO(input_data)):
            board.load_from_stdin()
            
        self.assertEqual(board.width, 4)
        self.assertEqual(board.height, 3)

    def test_dimension_mismatch(self):
        """בדיקה שהקוד נכשל כשאחת השורות קצרה מהשאר"""
        input_data = (
            "Board:\n"
            ". . .\n"
            ". .\n"  # שורה קצרה מדי
            ". . ."
        )
        board = ChessBoard()
        with patch('sys.stdin', StringIO(input_data)):
            with self.assertRaises(BoardValidationError):
                board.load_from_stdin()

    def test_invalid_character(self):
        """validation that the code fails when there is an unknown token (like wX or a single letter)"""
        input_data = (
            "Board:\n"
            ". . .\n"
            ". wX .\n" #invalid token
            ". . ."
        )
        board = ChessBoard()
        with patch('sys.stdin', StringIO(input_data)):
            with self.assertRaises(BoardValidationError):
                board.load_from_stdin()

    def test_empty_input(self):
        """validation that the code fails when the input is completely empty"""
        input_data = ""
        board = ChessBoard()
        with patch('sys.stdin', StringIO(input_data)):
            with self.assertRaises(BoardValidationError):
                board.load_from_stdin()

    def test_windows_line_endings(self):
        """validation that the code handles Windows line endings correctly"""
        input_data = "Board:\r\n. . .\r\n. . .\r\n. . ."
        board = ChessBoard()
        with patch('sys.stdin', StringIO(input_data)):
            board.load_from_stdin()
        
        self.assertEqual(board.width, 3)
        self.assertEqual(board.height, 3)

if __name__ == "__main__":
    unittest.main()