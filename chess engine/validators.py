from types_and_constants import Position
from movement_strategies import StrategyFactory

class MoveValidator:
    """Abstract base interface for all movement rules and conditions in the game."""
    def validate(self, engine: 'ChessEngine', src: Position, dst: Position) -> bool:
        raise NotImplementedError


class RedirectValidator(MoveValidator):
    """Rule: prevents redirecting a piece that is currently in transit."""
    def validate(self, engine: 'ChessEngine', src: Position, dst: Position) -> bool:
        for move in engine._pending_moves:
            if move['src'] == src:
                return False
        return True


class CooldownValidator(MoveValidator):
    """Rule: checks whether the cooldown period for the current square has elapsed."""
    def validate(self, engine: 'ChessEngine', src: Position, dst: Position) -> bool:
        return engine.current_time >= engine.cooldown_matrix[src.row][src.col]


class PieceMovementValidator(MoveValidator):
    """Rule: checks the physical movement legality of the piece according to its strategy."""
    def validate(self, engine: 'ChessEngine', src: Position, dst: Position) -> bool:
        piece = engine.board_matrix[src.row][src.col]
        if not piece:
            return False
        strategy = StrategyFactory.get_strategy(piece.piece_type)
        return strategy and strategy.is_valid(engine.board_matrix, src, dst)
    
class ConcurrencyValidator(MoveValidator):
    """New rule: prevents simultaneous movement of pieces of different colors."""
    def validate(self, engine: 'ChessEngine', src: Position, dst: Position) -> bool:
        moving_piece = engine.board_matrix[src.row][src.col]
        if not moving_piece:
            return False
            
        for move in engine._pending_moves:
            # If another piece of a different color is currently moving, block the move
            if move['piece'].color != moving_piece.color:
                return False
        return True