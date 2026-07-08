import pytest
import sys
from io import StringIO
from collections import deque
import main as main_module
from main import Command, ClickCommand, WaitCommand, parse_command_line, parse_board_line

# --- Your original tests ---

def test_command_base_class():
    cmd = Command()
    cmd.execute(None)

def test_successful_board_and_command_execution(monkeypatch, capsys):
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
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    main_module.main()
    output = capsys.readouterr().out
    assert ". wK\n. bK" in output

def test_pipeline_row_width_mismatch(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        "wK .\n"
        ". . .\n"
        "Commands:\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    with pytest.raises(SystemExit):
        main_module.main()
    assert "ERROR ROW_WIDTH_MISMATCH" in capsys.readouterr().out

def test_pipeline_unknown_token_error(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        "wK wX\n"
        "Commands:\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    with pytest.raises(SystemExit):
        main_module.main()
    assert "ERROR UNKNOWN_TOKEN" in capsys.readouterr().out

def test_command_parsing_resilience(monkeypatch, capsys):
    input_data = (
        "Board:\n"
        ".\n"
        "Commands:\n"
        "click text invalid\n"
        "wait abc\n"
        "print board\n"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    main_module.main()
    assert "." in capsys.readouterr().out

def test_pipeline_accepts_empty_lines_and_print_command(monkeypatch, capsys):
    input_data = "\nBoard:\n\n.\nCommands:\n\nprint board\n"
    monkeypatch.setattr(sys, "stdin", StringIO(input_data))
    main_module.main()
    assert "." in capsys.readouterr().out

# --- New complementary tests for internal parsing lines ---

def test_parse_board_line_empty():
    res, width = parse_board_line("", 5)
    assert res == []
    assert width == 5

def test_parse_command_line_empty():
    q = deque()
    parse_command_line("", q)
    assert len(q) == 0