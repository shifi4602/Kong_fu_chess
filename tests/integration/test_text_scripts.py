from pathlib import Path

import pytest

from kungfu_chess.io.board_parser import BoardParser
from kungfu_chess.rules.rule_engine import default_rule_engine
from texttests.script_runner import ScriptRunner

SCRIPTS_DIR = Path(__file__).parent / 'scripts'


@pytest.mark.parametrize('script_name', [
    '01_board_parsing.kfc',
    '02_click_to_move.kfc',
    '03_rook_moves.kfc',
    '04_invalid_moves.kfc',
    '05_capture.kfc',
    '06_game_over.kfc',
])
def test_kfc_script(script_name):
    text = (SCRIPTS_DIR / script_name).read_text(encoding='utf-8')
    runner = ScriptRunner(
        parser=BoardParser(),
        rule_engine=default_rule_engine(),
        travel_duration=1.0,
    )
    result = runner.run(text)
    assert result.passed, f'{script_name} failed:\n' + '\n'.join(result.failures)
