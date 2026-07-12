import sys

import kungfu_chess.config as config
from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper, Controller
from kungfu_chess.io import BoardParser, BoardPrinter
from kungfu_chess.model import GameState
from kungfu_chess.realtime import IClock, RealTimeArbiter
from kungfu_chess.rules import default_rule_engine


class _FakeClock(IClock):
    def __init__(self) -> None:
        self._time: float = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


def _parse_input(text: str):
    lines = text.splitlines()
    board_lines = []
    commands = []

    i = 0
    while i < len(lines) and lines[i].strip() != 'Board:':
        i += 1
    i += 1

    while i < len(lines) and lines[i].strip() != 'Commands:':
        line = lines[i].strip()
        if line:
            board_lines.append(line)
        i += 1
    i += 1

    while i < len(lines):
        line = lines[i].strip()
        if line:
            commands.append(line)
        i += 1

    return '\n'.join(board_lines), commands


def main() -> None:
    board_text, commands = _parse_input(sys.stdin.read())

    try:
        board = BoardParser().parse(board_text)
    except ValueError as e:
        msg = str(e)
        if 'tokens, expected' in msg:
            print('ERROR ROW_WIDTH_MISMATCH')
        else:
            print('ERROR UNKNOWN_TOKEN')
        return

    state = GameState(board=board)
    clock = _FakeClock()
    arbiter = RealTimeArbiter(clock, travel_duration=config.TRAVEL_DURATION)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    mapper = BoardMapper(
        cell_size=config.CELL_SIZE,
        rows=board.rows,
        cols=board.cols,
    )
    controller = Controller(engine, mapper)
    printer = BoardPrinter()

    for cmd in commands:
        parts = cmd.split()
        if not parts:
            continue

        if parts[0] == 'print' and len(parts) >= 2 and parts[1] == 'board':
            print(printer.render(engine.get_snapshot().board))

        elif parts[0] == 'click' and len(parts) == 3:
            controller.on_click(int(parts[1]), int(parts[2]))

        elif parts[0] == 'wait' and len(parts) == 2:
            clock.advance(int(parts[1]) / 1000.0)
            controller.on_tick()


if __name__ == '__main__':
    main()
