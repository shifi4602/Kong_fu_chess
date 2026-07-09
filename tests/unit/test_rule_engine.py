from kungfu_chess.model import Board, Color, GameState, Piece, PieceKind, PieceState, Position
from kungfu_chess.rules import (
    DestinationValidator,
    MovementValidator,
    MoveRequest,
    PieceExistsValidator,
    PieceIdleValidator,
    default_rule_engine,
)


def _piece(color=Color.WHITE, kind=PieceKind.KING, state=PieceState.IDLE) -> Piece:
    p = Piece(id='t', color=color, kind=kind, cell=Position(0, 0))
    p.state = state
    return p


def _state(rows=4, cols=4) -> GameState:
    return GameState(board=Board(rows, cols))


# --- PieceExistsValidator ---

def test_exists_empty_src():
    state = _state()
    v = PieceExistsValidator()
    assert not v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_exists_piece_at_src():
    state = _state()
    state.board.place(_piece(), Position(0, 0))
    v = PieceExistsValidator()
    assert v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


# --- PieceIdleValidator ---

def test_idle_moving_piece():
    state = _state()
    p = _piece(state=PieceState.MOVING)
    state.board.place(p, Position(0, 0))
    v = PieceIdleValidator()
    assert not v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_idle_idle_piece():
    state = _state()
    state.board.place(_piece(), Position(0, 0))
    v = PieceIdleValidator()
    assert v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_idle_no_piece_at_src():
    state = _state()
    v = PieceIdleValidator()
    assert not v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


# --- DestinationValidator ---

def test_dst_empty_allowed():
    state = _state()
    state.board.place(_piece(Color.WHITE), Position(0, 0))
    v = DestinationValidator()
    assert v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_dst_enemy_allowed():
    state = _state()
    state.board.place(_piece(Color.WHITE), Position(0, 0))
    state.board.place(_piece(Color.BLACK), Position(0, 1))
    v = DestinationValidator()
    assert v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_dst_same_color_rejected():
    state = _state()
    state.board.place(_piece(Color.WHITE, PieceKind.KING), Position(0, 0))
    state.board.place(_piece(Color.WHITE, PieceKind.ROOK), Position(0, 1))
    v = DestinationValidator()
    assert not v.validate(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_dst_out_of_bounds_rejected():
    state = _state(rows=4, cols=4)
    state.board.place(_piece(Color.WHITE), Position(0, 0))
    v = DestinationValidator()
    assert not v.validate(state, MoveRequest(Position(0, 0), Position(0, 10)))


# --- Full chain via default_rule_engine ---

def test_full_chain_valid_king_move():
    board = Board(8, 8)
    state = GameState(board=board)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(4, 4))
    board.place(wk, Position(4, 4))
    engine = default_rule_engine()
    assert engine.can_move(state, MoveRequest(Position(4, 4), Position(4, 5)))


def test_full_chain_invalid_king_move():
    board = Board(8, 8)
    state = GameState(board=board)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(4, 4))
    board.place(wk, Position(4, 4))
    engine = default_rule_engine()
    assert not engine.can_move(state, MoveRequest(Position(4, 4), Position(4, 6)))


def test_full_chain_no_piece():
    board = Board(8, 8)
    state = GameState(board=board)
    engine = default_rule_engine()
    assert not engine.can_move(state, MoveRequest(Position(0, 0), Position(0, 1)))


def test_full_chain_moving_piece_rejected():
    board = Board(8, 8)
    state = GameState(board=board)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(4, 4))
    wk.state = PieceState.MOVING
    board.place(wk, Position(4, 4))
    engine = default_rule_engine()
    assert not engine.can_move(state, MoveRequest(Position(4, 4), Position(4, 5)))
