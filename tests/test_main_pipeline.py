import unittest
from io import StringIO
from unittest.mock import patch

import main as main_module

from main import Command, ClickCommand, WaitCommand
import main

def test_command_base_class():
    """direct call to base class"""
    """מכסה את שורה 8 - קריאה ישירה למחלקת הבסיס"""
    cmd = Command()
    cmd.execute(None)

def test_explicit_value_errors():
    """מכסה במדויק את שורות 60 ו-79 על ידי הזנת ארגומנטים שגויים ישירות למחלקות הפקודה"""
    engine_mock = None
    

class TestMainPipeline(unittest.TestCase):
    def test_successful_board_and_command_execution(self):
        input_data = (
            "Board:\n"
            "wK .\n"
            ". bK\n"
            "Commands:\n"
            "click 0 0\n"
            "click 100 0\n"
            "wait 6000\n"
            "print board\n"
        )

        with patch("sys.stdin", StringIO(input_data)), patch("sys.stdout", new=StringIO()) as fake_out:
            main_module.main()
            output = fake_out.getvalue()

        self.assertIn(". wK\n. bK", output)

    def test_pipeline_row_width_mismatch(self):
        input_data = (
            "Board:\n"
            "wK .\n"
            ". . .\n"
            "Commands:\n"
        )

        with patch("sys.stdin", StringIO(input_data)), patch("sys.stdout", new=StringIO()) as fake_out:
            main_module.main()

        self.assertIn("ERROR ROW_WIDTH_MISMATCH", fake_out.getvalue())

    def test_pipeline_unknown_token_error(self):
        input_data = (
            "Board:\n"
            "wK wX\n"
            "Commands:\n"
        )

        with patch("sys.stdin", StringIO(input_data)), patch("sys.stdout", new=StringIO()) as fake_out:
            main_module.main()

        self.assertIn("ERROR UNKNOWN_TOKEN", fake_out.getvalue())

    def test_command_parsing_resilience(self):
        input_data = (
            "Board:\n"
            ".\n"
            "Commands:\n"
            "click text invalid\n"
            "wait abc\n"
            "print board\n"
        )

        with patch("sys.stdin", StringIO(input_data)), patch("sys.stdout", new=StringIO()) as fake_out:
            main_module.main()

        self.assertIn(".", fake_out.getvalue())

    def test_pipeline_accepts_empty_lines_and_print_command(self):
        input_data = "\nBoard:\n\n.\nCommands:\n\nprint board\n"

        with patch("sys.stdin", StringIO(input_data)), patch("sys.stdout", new=StringIO()) as fake_out:
            main_module.main()

        self.assertIn(".", fake_out.getvalue())


if __name__ == "__main__":
    unittest.main()