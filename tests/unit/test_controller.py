from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper, Controller
from kungfu_chess.model import Board, Color, GameState, Piece, PieceKind, PieceState, Position
from kungfu_chess.realtime import IClock, RealTimeArbiter
from kungfu_chess.rules import default_rule_engine

CELL = 100


class FakeClock(IClock):
    def __init__(self) -> None:
        self._time: float = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


def _px(col: int, row: int):
    return col * CELL, row * CELL


def _make_controller():
    board = Board(4, 4)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(3, 3))
    bk = Piece(id='bK', color=Color.BLACK, kind=PieceKind.KING, cell=Position(0, 0))
    wr = Piece(id='wR', color=Color.WHITE, kind=PieceKind.ROOK, cell=Position(3, 0))
    board.place(wk, Position(3, 3))
    board.place(bk, Position(0, 0))
    board.place(wr, Position(3, 0))
    state = GameState(board=board)
    clock = FakeClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    mapper = BoardMapper(cell_size=CELL, rows=4, cols=4)
    controller = Controller(engine, mapper)
    return controller, clock, engine


def test_first_click_selects_idle_piece():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(0, 3))  # wR at Position(row=3, col=0)
    assert ctrl.selected == Position(3, 0)


def test_second_click_moves_and_deselects():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(0, 3))  # select wR at (3,0)
    ctrl.on_click(*_px(1, 3))  # move to (3,1)
    assert ctrl.selected is None


def test_same_cell_twice_deselects():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(0, 3))  # select
    ctrl.on_click(*_px(0, 3))  # same cell
    assert ctrl.selected is None


def test_click_empty_cell_no_selection():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(1, 1))  # empty cell
    assert ctrl.selected is None


def test_click_out_of_bounds_ignored():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(9999, 9999)
    assert ctrl.selected is None


def test_failed_move_empty_dst_deselects():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(0, 3))  # select wR at (3,0)
    # Rook diagonal (3,0)→(2,1) is invalid; (2,1) is empty → deselect
    ctrl.on_click(*_px(1, 2))
    assert ctrl.selected is None


def test_failed_move_idle_piece_at_dst_reselects():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(0, 3))  # select wR at (3,0)
    # Rook diagonal (3,0)→(2,0) is invalid; wK at (3,3) is IDLE — but let's use bK at (0,0)
    # Rook going from (3,0) to (0,0) is a valid straight move. Use different invalid move.
    # wR at (3,0) → (2,1) is diagonal → rejected; (2,1) empty → deselect
    # Instead: rook (3,0)→(3,3): blocked by wK (same color) → rejected; wK is IDLE → re-select wK
    ctrl.on_click(*_px(3, 3))  # wK at (3,3): same color → move rejected; wK IDLE → re-select
    assert ctrl.selected == Position(3, 3)


def test_on_tick_advances_engine():
    ctrl, clock, engine = _make_controller()
    ctrl.on_click(*_px(0, 3))  # select wR at (3,0)
    ctrl.on_click(*_px(1, 3))  # move wR to (3,1)
    clock.advance(2.0)
    ctrl.on_tick()
    snap = engine.get_snapshot()
    assert snap.board.get(Position(3, 1)) is not None


def test_click_moving_piece_not_selected():
    ctrl, _, _ = _make_controller()
    ctrl.on_click(*_px(0, 3))  # select wR at (3,0)
    ctrl.on_click(*_px(1, 3))  # move wR → wR now MOVING
    # Try to select wR again while it's moving (it's not at (3,0) anymore in grid,
    # but the board still has it there until tick resolves)
    # Actually before tick, piece is still at src with state=MOVING
    ctrl.on_click(*_px(0, 3))  # wR is still at src, state=MOVING → should NOT select
    assert ctrl.selected is None
