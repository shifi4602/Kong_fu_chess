import unittest

from movement_strategies import (
    StrategyFactory,
    KingStrategy,
    RookStrategy,
    BishopStrategy,
    QueenStrategy,
    KnightStrategy,
    PawnStrategy,
)
from types_and_constants import Color, PieceType, Position, Piece


class TestMovementStrategies(unittest.TestCase):
    def setUp(self):
        self.board = [
            [Piece(Color.WHITE, PieceType.ROOK), None, Piece(Color.BLACK, PieceType.KING)],
            [None, Piece(Color.WHITE, PieceType.PAWN), None],
            [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
        ]

    def test_base_target_check_rejects_same_color_targets(self):
        strategy = KingStrategy()
        source = Position(0, 0)
        target = Position(2, 0)

        self.assertFalse(strategy._base_target_check(self.board, source, target))

    def test_base_target_check_allows_enemy_targets(self):
        strategy = KingStrategy()
        source = Position(0, 0)
        target = Position(0, 2)

        self.assertTrue(strategy._base_target_check(self.board, source, target))

    def test_king_strategy_allows_adjacent_moves(self):
        strategy = KingStrategy()

        self.assertTrue(strategy.is_valid(self.board, Position(0, 2), Position(1, 2)))
        self.assertFalse(strategy.is_valid(self.board, Position(0, 2), Position(2, 0)))

    def test_rook_strategy_requires_clear_path(self):
        strategy = RookStrategy()

        self.assertTrue(strategy.is_valid(self.board, Position(0, 0), Position(0, 1)))
        blocked_board = [
            [Piece(Color.WHITE, PieceType.ROOK), Piece(Color.BLACK, PieceType.PAWN), Piece(Color.BLACK, PieceType.KING)],
            [None, Piece(Color.WHITE, PieceType.PAWN), None],
            [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
        ]
        self.assertFalse(strategy.is_valid(blocked_board, Position(0, 0), Position(0, 2)))

    def test_bishop_strategy_requires_diagonal_path(self):
        strategy = BishopStrategy()

        valid_board = [
            [Piece(Color.WHITE, PieceType.ROOK), None, Piece(Color.BLACK, PieceType.KING)],
            [None, None, None],
            [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
        ]
        self.assertTrue(strategy.is_valid(valid_board, Position(2, 0), Position(1, 1)))
        self.assertFalse(strategy.is_valid(self.board, Position(2, 0), Position(1, 1)))
        self.assertFalse(strategy.is_valid(self.board, Position(2, 0), Position(2, 1)))

    def test_queen_strategy_supports_straight_and_diagonal_moves(self):
        strategy = QueenStrategy()

        self.assertTrue(strategy.is_valid(self.board, Position(0, 0), Position(0, 1)))
        valid_board = [
            [Piece(Color.WHITE, PieceType.QUEEN), None, Piece(Color.BLACK, PieceType.KING)],
            [None, None, None],
            [Piece(Color.WHITE, PieceType.BISHOP), None, Piece(Color.BLACK, PieceType.PAWN)],
        ]
        self.assertTrue(strategy.is_valid(valid_board, Position(0, 0), Position(1, 1)))
        self.assertFalse(strategy.is_valid(self.board, Position(0, 0), Position(1, 1)))
        self.assertFalse(strategy.is_valid(self.board, Position(0, 0), Position(1, 2)))

    def test_knight_strategy_allows_jump_moves(self):
        strategy = KnightStrategy()

        self.assertTrue(strategy.is_valid(self.board, Position(0, 0), Position(1, 2)))
        self.assertFalse(strategy.is_valid(self.board, Position(0, 0), Position(1, 1)))

    def test_pawn_strategy_moves_forward_and_captures_diagonally(self):
        strategy = PawnStrategy()
        white_pawn = Position(1, 1)

        self.assertTrue(strategy.is_valid(self.board, white_pawn, Position(0, 1)))
        self.assertTrue(strategy.is_valid(self.board, white_pawn, Position(0, 2)))

        self.board[0][1] = Piece(Color.BLACK, PieceType.PAWN)
        self.assertFalse(strategy.is_valid(self.board, white_pawn, Position(0, 1)))

        black_pawn_board = [
            [None, None, None],
            [None, Piece(Color.BLACK, PieceType.PAWN), None],
            [None, None, None],
        ]
        self.assertTrue(strategy.is_valid(black_pawn_board, Position(1, 1), Position(2, 1)))
        self.assertFalse(strategy.is_valid(black_pawn_board, Position(1, 1), Position(0, 1)))
        self.assertFalse(strategy.is_valid(black_pawn_board, Position(1, 1), Position(2, 2)))

    def test_strategy_factory_returns_expected_strategy_instance(self):
        self.assertIsInstance(StrategyFactory.get_strategy(PieceType.KING), KingStrategy)
        self.assertIsInstance(StrategyFactory.get_strategy(PieceType.ROOK), RookStrategy)
        self.assertIsInstance(StrategyFactory.get_strategy(PieceType.QUEEN), QueenStrategy)
        self.assertIsInstance(StrategyFactory.get_strategy(PieceType.BISHOP), BishopStrategy)
        self.assertIsInstance(StrategyFactory.get_strategy(PieceType.KNIGHT), KnightStrategy)
        self.assertIsInstance(StrategyFactory.get_strategy(PieceType.PAWN), PawnStrategy)


    def test_invalid_rook_and_bishop_moves(self):
        """the movment strategies for rook and bishop should reject invalid moves"""
        strat_rook = RookStrategy()
        # in valid diagonal move for rook - should return False on line 24
        self.assertFalse(strat_rook.is_valid(self.board, Position(0, 0), Position(1, 2)))

        strat_bishop = BishopStrategy()
        # in valid straight move for bishop - should return False on line 30
        self.assertFalse(strat_bishop.is_valid(self.board, Position(2, 0), Position(2, 2)))
        
        strat_queen = QueenStrategy()
        # in valid diagonal move for queen - should return False on line 39
        self.assertFalse(strat_queen.is_valid(self.board, Position(0, 0), Position(1, 2)))

if __name__ == "__main__":
    unittest.main()