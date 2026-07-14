from kungfu_chess.model import Board, Color, Piece, PieceKind, Position
from kungfu_chess.rules import (
    BishopRule, KingRule, KnightRule, MoveRequest, PawnRule, PieceRule, QueenRule, RookRule,
)


def _piece(color=Color.WHITE, kind=PieceKind.PAWN) -> Piece:
    return Piece(id='t', color=color, kind=kind, cell=Position(0, 0))


def _board(*placements):
    board = Board(8, 8)
    for piece, pos in placements:
        board.place(piece, pos)
    return board


# --- KingRule ---

def test_king_one_step_horizontal():
    rule = KingRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(4, 5)))


def test_king_one_step_diagonal():
    rule = KingRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(3, 3)))


def test_king_same_square():
    rule = KingRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(4, 4)))


def test_king_two_steps():
    rule = KingRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(4, 6)))


# --- RookRule ---

def test_rook_horizontal():
    rule = RookRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 0), Position(4, 7)))


def test_rook_vertical():
    rule = RookRule()
    assert rule.is_valid(_board(), MoveRequest(Position(0, 4), Position(7, 4)))


def test_rook_diagonal_rejected():
    rule = RookRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(0, 0), Position(4, 4)))


def test_rook_blocked_path():
    blocker = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((blocker, Position(4, 3)))
    rule = RookRule()
    assert not rule.is_valid(board, MoveRequest(Position(4, 0), Position(4, 7)))


def test_rook_same_square():
    rule = RookRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(4, 4)))


# --- BishopRule ---

def test_bishop_diagonal():
    rule = BishopRule()
    assert rule.is_valid(_board(), MoveRequest(Position(0, 0), Position(4, 4)))


def test_bishop_diagonal_back():
    rule = BishopRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(1, 1)))


def test_bishop_non_diagonal():
    rule = BishopRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(0, 0), Position(4, 3)))


def test_bishop_horizontal():
    rule = BishopRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(0, 0), Position(0, 4)))


def test_bishop_blocked_diagonal():
    blocker = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((blocker, Position(2, 2)))
    rule = BishopRule()
    assert not rule.is_valid(board, MoveRequest(Position(0, 0), Position(4, 4)))


# --- QueenRule ---

def test_queen_straight():
    rule = QueenRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(4, 0)))


def test_queen_diagonal():
    rule = QueenRule()
    assert rule.is_valid(_board(), MoveRequest(Position(0, 0), Position(4, 4)))


def test_queen_invalid_shape():
    rule = QueenRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(0, 0), Position(1, 2)))


# --- KnightRule ---

def test_knight_l_shape_2_1():
    rule = KnightRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(2, 3)))


def test_knight_l_shape_1_2():
    rule = KnightRule()
    assert rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(3, 2)))


def test_knight_straight():
    rule = KnightRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(4, 5)))


def test_knight_diagonal():
    rule = KnightRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(5, 5)))


# --- PawnRule ---

def test_pawn_white_forward():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    board = _board((wp, Position(4, 4)))
    rule = PawnRule()
    assert rule.is_valid(board, MoveRequest(Position(4, 4), Position(3, 4)))


def test_pawn_white_blocked():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    blocker = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((wp, Position(4, 4)), (blocker, Position(3, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(4, 4), Position(3, 4)))


def test_pawn_white_diagonal_capture():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    enemy = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((wp, Position(4, 4)), (enemy, Position(3, 5)))
    rule = PawnRule()
    assert rule.is_valid(board, MoveRequest(Position(4, 4), Position(3, 5)))


def test_pawn_white_diagonal_no_enemy():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    board = _board((wp, Position(4, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(4, 4), Position(3, 5)))


def test_pawn_white_diagonal_same_color():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    ally = _piece(Color.WHITE, PieceKind.ROOK)
    board = _board((wp, Position(4, 4)), (ally, Position(3, 5)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(4, 4), Position(3, 5)))


def test_pawn_black_forward():
    bp = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((bp, Position(3, 4)))
    rule = PawnRule()
    assert rule.is_valid(board, MoveRequest(Position(3, 4), Position(4, 4)))


def test_pawn_white_backward_rejected():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    board = _board((wp, Position(4, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(4, 4), Position(5, 4)))


def test_pawn_white_two_steps_rejected():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    board = _board((wp, Position(4, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(4, 4), Position(2, 4)))


def test_pawn_white_two_steps_from_start_row_allowed():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    board = _board((wp, Position(6, 4)))
    rule = PawnRule()
    assert rule.is_valid(board, MoveRequest(Position(6, 4), Position(4, 4)))


def test_pawn_white_two_steps_blocked_mid_path():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    blocker = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((wp, Position(6, 4)), (blocker, Position(5, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(6, 4), Position(4, 4)))


def test_pawn_white_two_steps_destination_occupied():
    wp = _piece(Color.WHITE, PieceKind.PAWN)
    blocker = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((wp, Position(6, 4)), (blocker, Position(4, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(6, 4), Position(4, 4)))


def test_pawn_black_two_steps_from_start_row_allowed():
    bp = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((bp, Position(1, 4)))
    rule = PawnRule()
    assert rule.is_valid(board, MoveRequest(Position(1, 4), Position(3, 4)))


def test_pawn_black_two_steps_not_from_start_row_rejected():
    bp = _piece(Color.BLACK, PieceKind.PAWN)
    board = _board((bp, Position(3, 4)))
    rule = PawnRule()
    assert not rule.is_valid(board, MoveRequest(Position(3, 4), Position(5, 4)))


def test_pawn_no_piece_at_src():
    rule = PawnRule()
    assert not rule.is_valid(_board(), MoveRequest(Position(4, 4), Position(3, 4)))


def test_piece_rule_abstract_body():
    result = PieceRule.is_valid(None, _board(), MoveRequest(Position(0, 0), Position(0, 1)))
    assert result is None
