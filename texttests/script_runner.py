from dataclasses import dataclass, field
from typing import List, Optional

from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.io.board_parser import BoardParser
from kungfu_chess.model.game_state import GameState
from kungfu_chess.model.piece import Color, PieceKind, PieceState
from kungfu_chess.model.position import Position
from kungfu_chess.realtime.real_time_arbiter import IClock, RealTimeArbiter
from kungfu_chess.rules.move_request import MoveRequest
from kungfu_chess.rules.rule_engine import RuleEngine

from .script_parser import ScriptCommand, ScriptParser


class _FakeClock(IClock):
    def __init__(self) -> None:
        self._time: float = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


_COLOR_CHAR = {Color.WHITE: 'w', Color.BLACK: 'b'}
_KIND_CHAR = {
    PieceKind.KING: 'K',
    PieceKind.QUEEN: 'Q',
    PieceKind.ROOK: 'R',
    PieceKind.BISHOP: 'B',
    PieceKind.KNIGHT: 'N',
    PieceKind.PAWN: 'P',
}
_COLOR_NAME = {'WHITE': Color.WHITE, 'BLACK': Color.BLACK}


@dataclass
class ScriptResult:
    passed: bool
    failures: List[str] = field(default_factory=list)


class ScriptRunner:
    def __init__(
        self,
        parser: BoardParser,
        rule_engine: RuleEngine,
        travel_duration: float = 1.0,
    ) -> None:
        self._board_parser = parser
        self._rule_engine = rule_engine
        self._travel_duration = travel_duration

    def run(self, script: str) -> ScriptResult:
        script_parser = ScriptParser()
        commands = script_parser.parse(script)
        failures: List[str] = []
        clock: Optional[_FakeClock] = None
        engine: Optional[GameEngine] = None
        selected: Optional[Position] = None

        for cmd in commands:
            if cmd.kind == 'BOARD':
                board = self._board_parser.parse(cmd.args[0])
                state = GameState(board=board)
                clock = _FakeClock()
                arbiter = RealTimeArbiter(clock, self._travel_duration)
                engine = GameEngine(state, self._rule_engine, arbiter)
                selected = None

            elif cmd.kind == 'CLICK':
                if engine is None:
                    failures.append('CLICK before BOARD')
                    continue
                row = int(cmd.args[0])
                col = int(cmd.args[1])
                pos = Position(row, col)
                if selected is None:
                    piece = engine.get_snapshot().board.get(pos)
                    if piece is None:
                        continue
                    if piece.state != PieceState.IDLE:
                        continue
                    selected = pos
                elif pos == selected:
                    selected = None
                elif engine.request_move(MoveRequest(selected, pos)):
                    selected = None
                else:
                    piece = engine.get_snapshot().board.get(pos)
                    if piece is not None and piece.state == PieceState.IDLE:
                        selected = pos
                    else:
                        selected = None

            elif cmd.kind == 'TICK':
                if engine is None or clock is None:
                    failures.append('TICK before BOARD')
                    continue
                seconds = float(cmd.args[0])
                clock.advance(seconds)
                engine.tick()

            elif cmd.kind == 'ASSERT_CELL':
                if engine is None:
                    failures.append('ASSERT_CELL before BOARD')
                    continue
                row = int(cmd.args[0])
                col = int(cmd.args[1])
                expected = cmd.args[2]
                pos = Position(row, col)
                piece = engine.get_snapshot().board.get(pos)
                if expected == '.':
                    if piece is not None:
                        actual = _COLOR_CHAR[piece.color] + _KIND_CHAR[piece.kind]
                        failures.append(
                            f'ASSERT_CELL ({row},{col}): expected empty, got {actual}'
                        )
                else:
                    if piece is None:
                        failures.append(
                            f'ASSERT_CELL ({row},{col}): expected {expected}, got empty'
                        )
                    else:
                        actual = _COLOR_CHAR[piece.color] + _KIND_CHAR[piece.kind]
                        if actual != expected:
                            failures.append(
                                f'ASSERT_CELL ({row},{col}): expected {expected}, got {actual}'
                            )

            elif cmd.kind == 'ASSERT_WINNER':
                if engine is None:
                    failures.append('ASSERT_WINNER before BOARD')
                    continue
                expected_name = cmd.args[0].upper()
                winner = engine.get_snapshot().winner
                if winner is None:
                    failures.append(f'ASSERT_WINNER {expected_name}: game not over yet')
                else:
                    actual_name = winner.value.upper()
                    if actual_name != expected_name:
                        failures.append(
                            f'ASSERT_WINNER: expected {expected_name}, got {actual_name}'
                        )

            elif cmd.kind == 'ASSERT_GAME_OVER':
                if engine is None:
                    failures.append('ASSERT_GAME_OVER before BOARD')
                    continue
                if not engine.get_snapshot().is_over:
                    failures.append('ASSERT_GAME_OVER: game is not over')

            elif cmd.kind == 'ASSERT_ALIVE':
                if engine is None:
                    failures.append('ASSERT_ALIVE before BOARD')
                    continue
                if engine.get_snapshot().is_over:
                    winner = engine.get_snapshot().winner
                    failures.append(f'ASSERT_ALIVE: game is over, winner={winner}')

        passed = len(failures) == 0
        return ScriptResult(passed=passed, failures=failures)
