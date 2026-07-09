from kungfu_chess.model import Board, Color, GameState, Piece, PieceKind, PieceState, Position
from kungfu_chess.realtime import IClock, Motion, RealTimeArbiter, SystemClock


class FakeClock(IClock):
    def __init__(self) -> None:
        self._time: float = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


def _piece(color=Color.WHITE, kind=PieceKind.ROOK) -> Piece:
    return Piece(id='t', color=color, kind=kind, cell=Position(0, 0))


def _setup(rows=4, cols=4):
    board = Board(rows, cols)
    state = GameState(board=board)
    clock = FakeClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    return board, state, clock, arbiter


def test_start_motion_sets_moving_state():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    assert piece.state == PieceState.MOVING


def test_start_motion_adds_to_active():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    assert len(arbiter.active_motions()) == 1


def test_tick_completes_motion():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(2.0)
    arbiter.tick(state)
    assert board.get(Position(0, 3)) is piece
    assert board.get(Position(0, 0)) is None
    assert piece.state == PieceState.IDLE


def test_tick_removes_from_active_on_completion():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(2.0)
    arbiter.tick(state)
    assert len(arbiter.active_motions()) == 0


def test_tick_incomplete_motion_stays_at_src():
    board, state, clock, arbiter = _setup()
    arbiter._travel_duration = 5.0
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(0.5)
    arbiter.tick(state)
    assert board.get(Position(0, 0)) is piece
    assert len(arbiter.active_motions()) == 1
    assert piece.state == PieceState.MOVING


def test_capture_on_arrival():
    board, state, clock, arbiter = _setup()
    attacker = _piece(Color.WHITE, PieceKind.ROOK)
    defender = _piece(Color.BLACK, PieceKind.KING)
    board.place(attacker, Position(0, 0))
    board.place(defender, Position(0, 3))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(2.0)
    arbiter.tick(state)
    assert board.get(Position(0, 3)) is attacker
    assert defender.state == PieceState.CAPTURED


def test_identity_check_skips_src_removal_if_replaced():
    board, state, clock, arbiter = _setup()
    original = _piece(Color.WHITE, PieceKind.ROOK)
    interloper = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(original, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    board.place(interloper, Position(0, 0))
    clock.advance(2.0)
    arbiter.tick(state)
    assert board.get(Position(0, 0)) is interloper


def test_active_motions_returns_copy():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    motions = arbiter.active_motions()
    motions.clear()
    assert len(arbiter.active_motions()) == 1


def test_iclock_abstract_body():
    result = IClock.now(None)
    assert result is None


def test_system_clock_returns_positive_time():
    clock = SystemClock()
    assert clock.now() > 0.0


def test_motion_progress_before_start():
    piece = _piece()
    m = Motion(piece=piece, src=Position(0, 0), dst=Position(0, 3), start_time=1.0, duration=2.0)
    assert m.progress(0.5) == 0.0


def test_motion_progress_at_completion():
    piece = _piece()
    m = Motion(piece=piece, src=Position(0, 0), dst=Position(0, 3), start_time=0.0, duration=2.0)
    assert m.progress(2.0) == 1.0


def test_motion_progress_midway():
    piece = _piece()
    m = Motion(piece=piece, src=Position(0, 0), dst=Position(0, 3), start_time=0.0, duration=2.0)
    assert m.progress(1.0) == 0.5
