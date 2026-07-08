import pytest
from movement_strategies import (
    StrategyFactory, KingStrategy, RookStrategy, BishopStrategy, QueenStrategy, KnightStrategy, PawnStrategy
)
from types_and_constants import Color, PieceType, Position, Piece

@pytest.fixture
def board():
    return [
        [Piece(Color.WHITE, PieceType.ROOK), None, Piece(Color.BLACK, PieceType.KING)],
        [None, Piece(Color.WHITE, PieceType.PAWN), None],
        [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
    ]

# --- Your original tests (translated to pytest) ---

def test_base_target_check_rejects_same_color_targets(board):
    strategy = KingStrategy()
    assert not strategy._base_target_check(board, Position(0, 0), Position(2, 0))

def test_base_target_check_allows_enemy_targets(board):
    strategy = KingStrategy()
    assert strategy._base_target_check(board, Position(0, 0), Position(0, 2))

def test_king_strategy_allows_adjacent_moves(board):
    strategy = KingStrategy()
    assert strategy.is_valid(board, Position(0, 2), Position(1, 2))
    assert not strategy.is_valid(board, Position(0, 2), Position(2, 0))

def test_rook_strategy_requires_clear_path(board):
    strategy = RookStrategy()
    assert strategy.is_valid(board, Position(0, 0), Position(0, 1))
    blocked_board = [
        [Piece(Color.WHITE, PieceType.ROOK), Piece(Color.BLACK, PieceType.PAWN), Piece(Color.BLACK, PieceType.KING)],
        [None, Piece(Color.WHITE, PieceType.PAWN), None],
        [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
    ]
    assert not strategy.is_valid(blocked_board, Position(0, 0), Position(0, 2))

def test_bishop_strategy_requires_diagonal_path(board):
    strategy = BishopStrategy()
    valid_board = [
        [Piece(Color.WHITE, PieceType.ROOK), None, Piece(Color.BLACK, PieceType.KING)],
        [None, None, None],
        [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
    ]
    assert strategy.is_valid(valid_board, Position(2, 0), Position(1, 1))
    assert not strategy.is_valid(board, Position(2, 0), Position(1, 1))
    assert not strategy.is_valid(board, Position(2, 0), Position(2, 1))

def test_queen_strategy_supports_straight_and_diagonal_moves(board):
    strategy = QueenStrategy()
    assert strategy.is_valid(board, Position(0, 0), Position(0, 1))
    valid_board = [
        [Piece(Color.WHITE, PieceType.QUEEN), None, Piece(Color.BLACK, PieceType.KING)],
        [None, None, None],
        [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
    ]
    assert strategy.is_valid(valid_board, Position(0, 0), Position(1, 1))
    assert not strategy.is_valid(board, Position(0, 0), Position(1, 1))
    assert not strategy.is_valid(board, Position(0, 0), Position(1, 2))

def test_knight_strategy_allows_jump_moves(board):
    strategy = KnightStrategy()
    assert strategy.is_valid(board, Position(0, 0), Position(1, 2))
    assert not strategy.is_valid(board, Position(0, 0), Position(1, 1))

def test_pawn_strategy_moves_forward_and_captures_diagonally(board):
    strategy = PawnStrategy()
    white_pawn = Position(1, 1)
    assert strategy.is_valid(board, white_pawn, Position(0, 1))
    assert strategy.is_valid(board, white_pawn, Position(0, 2))

    board[0][1] = Piece(Color.BLACK, PieceType.PAWN)
    assert not strategy.is_valid(board, white_pawn, Position(0, 1))

    black_pawn_board = [
        [None, None, None],
        [None, Piece(Color.BLACK, PieceType.PAWN), None],
        [None, None, None],
    ]
    assert strategy.is_valid(black_pawn_board, Position(1, 1), Position(2, 1))
    assert not strategy.is_valid(black_pawn_board, Position(1, 1), Position(0, 1))
    assert not strategy.is_valid(black_pawn_board, Position(1, 1), Position(2, 2))

def test_strategy_factory_returns_expected_strategy_instance():
    assert isinstance(StrategyFactory.get_strategy(PieceType.KING), KingStrategy)
    assert isinstance(StrategyFactory.get_strategy(PieceType.ROOK), RookStrategy)
    assert isinstance(StrategyFactory.get_strategy(PieceType.QUEEN), QueenStrategy)
    assert isinstance(StrategyFactory.get_strategy(PieceType.BISHOP), BishopStrategy)
    assert isinstance(StrategyFactory.get_strategy(PieceType.KNIGHT), KnightStrategy)
    assert isinstance(StrategyFactory.get_strategy(PieceType.PAWN), PawnStrategy)

def test_invalid_rook_and_bishop_moves(board):
    strat_rook = RookStrategy()
    assert not strat_rook.is_valid(board, Position(0, 0), Position(1, 2))
    strat_bishop = BishopStrategy()
    assert not strat_bishop.is_valid(board, Position(2, 0), Position(2, 2))
    strat_queen = QueenStrategy()
    assert not strat_queen.is_valid(board, Position(0, 0), Position(1, 2))

# --- New supplementary tests for full coverage ---

def test_pawn_invalid_cases(board):
    strategy = PawnStrategy()
    # Backward or sideways pawn moves are illegal
    # Use squares that exist on the 3x3 board so we don't crash (IndexError)
    assert not strategy.is_valid(board, Position(1, 1), Position(1, 2))  # sideways move
    assert not strategy.is_valid(board, Position(1, 1), Position(2, 1))  # backward move (for a white pawn that should move up)