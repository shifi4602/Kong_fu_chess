import runpy
import sys
from io import StringIO
from pathlib import Path

import main as main_module

MAIN_PATH = Path(__file__).resolve().parents[2] / 'main.py'


# --- _parse_input ---

def test_parse_input_extracts_board_and_commands():
    text = (
        "Board:\n"
        "wK .\n"
        ". bK\n"
        "Commands:\n"
        "print board\n"
        "wait 100\n"
    )
    board_text, commands = main_module._parse_input(text)
    assert board_text == "wK .\n. bK"
    assert commands == ["print board", "wait 100"]


def test_parse_input_skips_leading_blank_lines_before_board_marker():
    text = "\n\nBoard:\n.\nCommands:\n"
    board_text, commands = main_module._parse_input(text)
    assert board_text == "."
    assert commands == []


# --- Happy paths ---

def test_click_to_move_and_print_board(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        "wK .\n"
        ". bK\n"
        "Commands:\n"
        "click 0 0\n"
        "click 100 0\n"
        "wait 2000\n"
        "print board\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    main_module.main()
    output = capsys.readouterr().out
    assert ". wK\n. bK" in output


def test_jump_command_leaves_piece_in_place(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        "wK .\n"
        ". bK\n"
        "Commands:\n"
        "jump 0 0\n"
        "wait 2000\n"
        "print board\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    main_module.main()
    output = capsys.readouterr().out
    assert "wK .\n. bK" in output


def test_script_entry_point_executes_main(monkeypatch, capsys):
    input_data = "Board:\nwK .\n. bK\nCommands:\nprint board\n"
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    runpy.run_path(str(MAIN_PATH), run_name="__main__")
    output = capsys.readouterr().out
    assert "wK .\n. bK" in output


# --- Unhappy paths ---

def test_row_width_mismatch_error(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        "wK .\n"
        ". . .\n"
        "Commands:\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    result = main_module.main()
    assert result is None
    assert "ERROR ROW_WIDTH_MISMATCH" in capsys.readouterr().out


def test_unknown_token_error(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        "wK wX\n"
        "Commands:\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    result = main_module.main()
    assert result is None
    assert "ERROR UNKNOWN_TOKEN" in capsys.readouterr().out


def test_blank_command_line_is_skipped(monkeypatch, capsys):
    monkeypatch.setattr(
        main_module,
        "_parse_input",
        lambda text: ("wK .\n. bK", ["", "print board"]),
    )
    monkeypatch.setattr(sys, "stdin", StringIO("irrelevant"))
    main_module.main()
    output = capsys.readouterr().out
    assert "wK .\n. bK" in output
