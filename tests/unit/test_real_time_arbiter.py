from kungfu_chess.model import Board, Color, GameState, Piece, PieceKind, PieceState, Position
from kungfu_chess.realtime import IClock, JumpAction, Motion, RealTimeArbiter, SystemClock


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
    clock.advance(3.0)
    arbiter.tick(state)
    assert board.get(Position(0, 3)) is piece
    assert board.get(Position(0, 0)) is None
    assert piece.state == PieceState.IDLE


def test_tick_removes_from_active_on_completion():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(3.0)
    arbiter.tick(state)
    assert len(arbiter.active_motions()) == 0


def test_motion_duration_scales_with_distance():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(2.0)
    arbiter.tick(state)
    assert board.get(Position(0, 0)) is piece
    assert board.get(Position(0, 3)) is None
    assert piece.state == PieceState.MOVING


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
    clock.advance(3.0)
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
    clock.advance(3.0)
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
    m = Motion(piece=piece, src=Position(0, 0), dst=Position(0, 3), path=(Position(0, 3),), start_time=1.0, duration=2.0, sequence=0)
    assert m.progress(0.5) == 0.0


def test_motion_progress_at_completion():
    piece = _piece()
    m = Motion(piece=piece, src=Position(0, 0), dst=Position(0, 3), path=(Position(0, 3),), start_time=0.0, duration=2.0, sequence=0)
    assert m.progress(2.0) == 1.0


def test_motion_progress_midway():
    piece = _piece()
    m = Motion(piece=piece, src=Position(0, 0), dst=Position(0, 3), path=(Position(0, 3),), start_time=0.0, duration=2.0, sequence=0)
    assert m.progress(1.0) == 0.5


# --- Friendly-landing conflicts ---

def test_friendly_landing_conflict_stops_one_square_short():
    board, state, clock, arbiter = _setup()
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    friend = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(mover, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    board.place(friend, Position(0, 3))
    clock.advance(3.0)
    arbiter.tick(state)
    assert board.get(Position(0, 0)) is None
    assert board.get(Position(0, 2)) is mover
    assert mover.state == PieceState.IDLE
    assert board.get(Position(0, 3)) is friend
    assert friend.state == PieceState.IDLE


def test_friendly_landing_conflict_leaves_active_motions_empty():
    board, state, clock, arbiter = _setup()
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    friend = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(mover, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    board.place(friend, Position(0, 3))
    clock.advance(3.0)
    arbiter.tick(state)
    assert len(arbiter.active_motions()) == 0


def test_enemy_race_to_same_square_still_captures():
    board, state, clock, arbiter = _setup()
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    enemy = _piece(Color.BLACK, PieceKind.PAWN)
    board.place(mover, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    board.place(enemy, Position(0, 3))
    clock.advance(3.0)
    arbiter.tick(state)
    assert board.get(Position(0, 3)) is mover
    assert enemy.state == PieceState.CAPTURED


def test_swapping_enemies_collide_and_capture_at_crossing_square():
    board, state, clock, arbiter = _setup()
    white = _piece(Color.WHITE, PieceKind.ROOK)
    black = _piece(Color.BLACK, PieceKind.ROOK)
    board.place(white, Position(0, 0))
    board.place(black, Position(0, 3))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    arbiter.start_motion(state, Position(0, 3), Position(0, 0))
    clock.advance(3.0)
    arbiter.tick(state)
    assert board.get(Position(0, 2)) is white
    assert board.get(Position(0, 0)) is None
    assert board.get(Position(0, 3)) is None
    assert black.state == PieceState.CAPTURED


# --- Mid-flight collisions ---

def test_mid_path_friendly_block_stops_one_square_short():
    board, state, clock, arbiter = _setup(rows=1, cols=5)
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    friend = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(mover, Position(0, 0))
    board.place(friend, Position(0, 2))
    arbiter.start_motion(state, Position(0, 0), Position(0, 4))
    clock.advance(3.0)
    arbiter.tick(state)
    assert board.get(Position(0, 1)) is mover
    assert mover.state == PieceState.IDLE
    assert board.get(Position(0, 2)) is friend
    assert len(arbiter.active_motions()) == 0


def test_mid_path_enemy_is_captured_and_motion_ends_there():
    board, state, clock, arbiter = _setup(rows=1, cols=5)
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    enemy = _piece(Color.BLACK, PieceKind.PAWN)
    board.place(mover, Position(0, 0))
    board.place(enemy, Position(0, 2))
    arbiter.start_motion(state, Position(0, 0), Position(0, 4))
    clock.advance(3.0)
    arbiter.tick(state)
    assert board.get(Position(0, 2)) is mover
    assert enemy.state == PieceState.CAPTURED
    assert board.get(Position(0, 4)) is None
    assert len(arbiter.active_motions()) == 0


def test_coarse_tick_after_large_wait_still_stops_at_mid_path_block():
    board, state, clock, arbiter = _setup(rows=1, cols=5)
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    friend = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(mover, Position(0, 0))
    board.place(friend, Position(0, 2))
    arbiter.start_motion(state, Position(0, 0), Position(0, 4))
    clock.advance(100.0)
    arbiter.tick(state)
    assert board.get(Position(0, 1)) is mover
    assert mover.state == PieceState.IDLE
    assert board.get(Position(0, 2)) is friend


def test_crossing_paths_same_color_later_mover_stops_short():
    board, state, clock, arbiter = _setup(rows=5, cols=5)
    queen = _piece(Color.WHITE, PieceKind.QUEEN)
    rook = _piece(Color.WHITE, PieceKind.ROOK)
    board.place(queen, Position(2, 0))
    board.place(rook, Position(0, 2))
    arbiter.start_motion(state, Position(2, 0), Position(2, 4))
    clock.advance(0.5)
    arbiter.start_motion(state, Position(0, 2), Position(4, 2))
    clock.advance(4.0)
    arbiter.tick(state)
    assert board.get(Position(2, 4)) is queen
    assert queen.state == PieceState.IDLE
    assert board.get(Position(1, 2)) is rook
    assert rook.state == PieceState.IDLE
    assert board.get(Position(2, 2)) is None
    assert len(arbiter.active_motions()) == 0


def test_crossing_paths_different_color_later_mover_captures():
    board, state, clock, arbiter = _setup(rows=5, cols=5)
    queen = _piece(Color.WHITE, PieceKind.QUEEN)
    rook = _piece(Color.BLACK, PieceKind.ROOK)
    board.place(queen, Position(2, 0))
    board.place(rook, Position(0, 2))
    arbiter.start_motion(state, Position(2, 0), Position(2, 4))
    clock.advance(0.5)
    arbiter.start_motion(state, Position(0, 2), Position(4, 2))
    clock.advance(4.0)
    arbiter.tick(state)
    assert board.get(Position(2, 2)) is rook
    assert rook.state == PieceState.IDLE
    assert queen.state == PieceState.CAPTURED
    assert board.get(Position(2, 0)) is None
    assert len(arbiter.active_motions()) == 0


def test_exact_tie_broken_by_creation_order():
    board, state, clock, arbiter = _setup(rows=5, cols=5)
    rook = _piece(Color.WHITE, PieceKind.ROOK)
    queen = _piece(Color.WHITE, PieceKind.QUEEN)
    board.place(rook, Position(0, 2))
    board.place(queen, Position(2, 0))
    arbiter.start_motion(state, Position(0, 2), Position(4, 2))
    arbiter.start_motion(state, Position(2, 0), Position(2, 4))
    clock.advance(4.0)
    arbiter.tick(state)
    assert board.get(Position(4, 2)) is rook
    assert rook.state == PieceState.IDLE
    assert board.get(Position(2, 1)) is queen
    assert queen.state == PieceState.IDLE


def test_pawn_mid_path_capture_regression():
    board, state, clock, arbiter = _setup()
    pawn = _piece(Color.WHITE, PieceKind.PAWN)
    enemy = _piece(Color.BLACK, PieceKind.PAWN)
    board.place(pawn, Position(2, 2))
    board.place(enemy, Position(1, 3))
    arbiter.start_motion(state, Position(2, 2), Position(1, 3))
    clock.advance(1.0)
    arbiter.tick(state)
    assert board.get(Position(1, 3)) is pawn
    assert enemy.state == PieceState.CAPTURED


def test_knight_motion_has_no_intermediate_squares():
    board, state, clock, arbiter = _setup(rows=5, cols=5)
    knight = _piece(Color.WHITE, PieceKind.KNIGHT)
    board.place(knight, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(2, 1))
    clock.advance(2.0)
    arbiter.tick(state)
    assert board.get(Position(2, 1)) is knight
    assert board.get(Position(0, 0)) is None
    assert knight.state == PieceState.IDLE
    assert len(arbiter.active_motions()) == 0


def test_jump_defense_triggers_at_mid_path_square():
    board, state, clock, arbiter = _setup(rows=1, cols=5)
    arbiter._jump_duration = 5.0
    defender = _piece(Color.BLACK, PieceKind.KING)
    mover = _piece(Color.WHITE, PieceKind.ROOK)
    board.place(defender, Position(0, 2))
    board.place(mover, Position(0, 0))
    arbiter.start_jump(state, Position(0, 2))
    arbiter.start_motion(state, Position(0, 0), Position(0, 4))
    clock.advance(3.0)
    arbiter.tick(state)
    assert mover.state == PieceState.CAPTURED
    assert board.get(Position(0, 0)) is None
    assert board.get(Position(0, 2)) is defender
    assert defender.state == PieceState.JUMPING
    assert len(arbiter.active_motions()) == 0


# --- Pawn promotion ---

def test_pawn_promotion_white_on_last_row():
    board, state, clock, arbiter = _setup(rows=4, cols=4)
    pawn = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(pawn, Position(1, 0))
    arbiter.start_motion(state, Position(1, 0), Position(0, 0))
    clock.advance(2.0)
    arbiter.tick(state)
    assert pawn.kind == PieceKind.QUEEN


def test_pawn_promotion_black_on_last_row():
    board, state, clock, arbiter = _setup(rows=4, cols=4)
    pawn = _piece(Color.BLACK, PieceKind.PAWN)
    board.place(pawn, Position(2, 0))
    arbiter.start_motion(state, Position(2, 0), Position(3, 0))
    clock.advance(2.0)
    arbiter.tick(state)
    assert pawn.kind == PieceKind.QUEEN


def test_pawn_no_promotion_before_last_row():
    board, state, clock, arbiter = _setup(rows=4, cols=4)
    pawn = _piece(Color.WHITE, PieceKind.PAWN)
    board.place(pawn, Position(2, 0))
    arbiter.start_motion(state, Position(2, 0), Position(1, 0))
    clock.advance(2.0)
    arbiter.tick(state)
    assert pawn.kind == PieceKind.PAWN


def test_non_pawn_arrival_on_last_row_no_promotion():
    board, state, clock, arbiter = _setup(rows=4, cols=4)
    rook = _piece(Color.WHITE, PieceKind.ROOK)
    board.place(rook, Position(1, 0))
    arbiter.start_motion(state, Position(1, 0), Position(0, 0))
    clock.advance(2.0)
    arbiter.tick(state)
    assert rook.kind == PieceKind.ROOK


# --- Jump ---

def test_start_jump_sets_jumping_state():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    assert piece.state == PieceState.JUMPING


def test_start_jump_adds_to_active_jumps():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    assert len(arbiter.active_jumps()) == 1


def test_active_jumps_returns_copy():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    jumps = arbiter.active_jumps()
    jumps.clear()
    assert len(arbiter.active_jumps()) == 1


def test_jump_stays_airborne_before_duration_elapses():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 5.0
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    clock.advance(0.5)
    arbiter.tick(state)
    assert piece.state == PieceState.JUMPING
    assert len(arbiter.active_jumps()) == 1


def test_jump_lands_normally_after_duration():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 1.0
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    clock.advance(1.0)
    arbiter.tick(state)
    assert piece.state == PieceState.IDLE
    assert board.get(Position(0, 0)) is piece
    assert len(arbiter.active_jumps()) == 0


def test_jump_defends_against_arriving_enemy():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 5.0
    defender = _piece(Color.BLACK, PieceKind.KING)
    attacker = _piece(Color.WHITE, PieceKind.ROOK)
    board.place(defender, Position(0, 3))
    board.place(attacker, Position(0, 0))
    arbiter.start_jump(state, Position(0, 3))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(3.0)
    arbiter.tick(state)
    assert attacker.state == PieceState.CAPTURED
    assert board.get(Position(0, 0)) is None
    assert board.get(Position(0, 3)) is defender
    assert defender.state == PieceState.JUMPING


def test_jump_defense_removes_attacker_from_active_motions():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 5.0
    defender = _piece(Color.BLACK, PieceKind.KING)
    attacker = _piece(Color.WHITE, PieceKind.ROOK)
    board.place(defender, Position(0, 3))
    board.place(attacker, Position(0, 0))
    arbiter.start_jump(state, Position(0, 3))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    clock.advance(3.0)
    arbiter.tick(state)
    assert len(arbiter.active_motions()) == 0


def test_arrival_after_jump_lands_captures_normally():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 1.0
    defender = _piece(Color.BLACK, PieceKind.KING)
    attacker = _piece(Color.WHITE, PieceKind.ROOK)
    board.place(defender, Position(0, 3))
    board.place(attacker, Position(0, 0))
    arbiter.start_jump(state, Position(0, 3))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))

    clock.advance(1.0)
    arbiter.tick(state)
    assert defender.state == PieceState.IDLE

    clock.advance(2.5)
    arbiter.tick(state)
    assert board.get(Position(0, 3)) is attacker
    assert defender.state == PieceState.CAPTURED


def test_jump_action_is_complete():
    piece = _piece()
    j = JumpAction(piece=piece, cell=Position(0, 0), start_time=0.0, duration=1.0)
    assert not j.is_complete(0.5)
    assert j.is_complete(1.0)


# --- Jump cooldown ---

def test_can_jump_true_when_never_jumped():
    board, state, clock, arbiter = _setup()
    piece = _piece()
    board.place(piece, Position(0, 0))
    assert arbiter.can_jump(piece)


def test_can_jump_false_immediately_after_landing():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 1.0
    arbiter._jump_cooldown = 1.0
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    clock.advance(1.0)
    arbiter.tick(state)
    assert not arbiter.can_jump(piece)


def test_can_jump_true_after_cooldown_elapses():
    board, state, clock, arbiter = _setup()
    arbiter._jump_duration = 1.0
    arbiter._jump_cooldown = 1.0
    piece = _piece()
    board.place(piece, Position(0, 0))
    arbiter.start_jump(state, Position(0, 0))
    clock.advance(1.0)
    arbiter.tick(state)
    clock.advance(1.0)
    assert arbiter.can_jump(piece)


def test_default_jump_cooldown_is_one_second():
    board, state, clock, arbiter = _setup()
    assert arbiter._jump_cooldown == 1.0
