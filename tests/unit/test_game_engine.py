from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.model.board import Board
from kungfu_chess.model.game_state import GameState
from kungfu_chess.model.piece import Color, Piece, PieceKind, PieceState
from kungfu_chess.model.position import Position
from kungfu_chess.realtime.real_time_arbiter import IClock, RealTimeArbiter
from kungfu_chess.rules.move_request import MoveRequest
from kungfu_chess.rules.rule_engine import default_rule_engine


class FakeClock(IClock):
    def __init__(self) -> None:
        self._time: float = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


def _make_engine(board: Board):
    state = GameState(board=board)
    clock = FakeClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    return engine, clock


def _board_with_kings():
    board = Board(4, 4)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(3, 3))
    bk = Piece(id='bK', color=Color.BLACK, kind=PieceKind.KING, cell=Position(0, 0))
    board.place(wk, Position(3, 3))
    board.place(bk, Position(0, 0))
    return board


def test_request_move_valid_returns_true():
    board = _board_with_kings()
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wr, Position(3, 0))
    engine, _ = _make_engine(board)
    result = engine.request_move(MoveRequest(Position(3, 0), Position(3, 1)))
    assert result


def test_request_move_starts_motion():
    board = _board_with_kings()
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wr, Position(3, 0))
    engine, _ = _make_engine(board)
    engine.request_move(MoveRequest(Position(3, 0), Position(3, 1)))
    assert wr.state == PieceState.MOVING


def test_request_move_invalid_returns_false():
    board = _board_with_kings()
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wr, Position(3, 0))
    engine, _ = _make_engine(board)
    result = engine.request_move(MoveRequest(Position(3, 0), Position(1, 1)))
    assert not result


def test_tick_resolves_completed_motion():
    board = _board_with_kings()
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wr, Position(3, 0))
    engine, clock = _make_engine(board)
    engine.request_move(MoveRequest(Position(3, 0), Position(3, 1)))
    clock.advance(2.0)
    engine.tick()
    snap = engine.get_snapshot()
    assert snap.board.get(Position(3, 1)) is wr
    assert snap.board.get(Position(3, 0)) is None


def test_game_over_black_king_captured():
    board = Board(4, 4)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(3, 3))
    bk = Piece(id='bK', color=Color.BLACK, kind=PieceKind.KING, cell=Position(0, 0))
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wk, Position(3, 3))
    board.place(bk, Position(0, 0))
    board.place(wr, Position(3, 0))
    engine, clock = _make_engine(board)
    engine.request_move(MoveRequest(Position(3, 0), Position(0, 0)))
    clock.advance(2.0)
    engine.tick()
    snap = engine.get_snapshot()
    assert snap.winner == Color.WHITE
    assert snap.is_over


def test_game_not_over_with_both_kings():
    board = _board_with_kings()
    engine, _ = _make_engine(board)
    engine.tick()
    snap = engine.get_snapshot()
    assert not snap.is_over
    assert snap.winner is None


def test_request_move_after_game_over_rejected():
    board = Board(4, 4)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(3, 3))
    board.place(wk, Position(3, 3))
    engine, _ = _make_engine(board)
    engine.tick()  # no black king → game over
    snap = engine.get_snapshot()
    assert snap.is_over
    result = engine.request_move(MoveRequest(Position(3, 3), Position(3, 2)))
    assert not result


def test_get_snapshot_reflects_motions():
    board = _board_with_kings()
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wr, Position(3, 0))
    engine, _ = _make_engine(board)
    engine.request_move(MoveRequest(Position(3, 0), Position(3, 1)))
    snap = engine.get_snapshot()
    assert len(snap.motions) == 1
