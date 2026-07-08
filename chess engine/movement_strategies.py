from abc import ABC, abstractmethod
from types_and_constants import Color, PieceType, Position

class MovementStrategy(ABC):
    @abstractmethod
    def is_valid(self, board: list, src: Position, dst: Position) -> bool:
        pass

    def _base_target_check(self, board: list, src: Position, dst: Position) -> bool:
        """Validates the target square: prevents hitting a piece of the same color."""
        src_piece = board[src.row][src.col]
        dst_piece = board[dst.row][dst.col]
        if dst_piece is not None and dst_piece.color == src_piece.color:
            return False
        return True

    def _is_path_clear(self, board: list, src: Position, dst: Position, step_r: int, step_c: int) -> bool:
        """Check for Blockers along the route - excluding the target slot."""
        curr_r, curr_c = src.row + step_r, src.col + step_c
        while (curr_r, curr_c) != (dst.row, dst.col):
            if board[curr_r][curr_c] is not None:
                return False
            curr_r += step_r
            curr_c += step_c
        return True

class KingStrategy(MovementStrategy):
    def is_valid(self, board, src, dst) -> bool:
        if not self._base_target_check(board, src, dst):
            return False
        return abs(dst.row - src.row) <= 1 and abs(dst.col - src.col) <= 1

class RookStrategy(MovementStrategy):
    def is_valid(self, board, src, dst) -> bool:
        if not self._base_target_check(board, src, dst):
            return False
        diff_r, diff_c = dst.row - src.row, dst.col - src.col
        if diff_r != 0 and diff_c != 0:
            return False
        step_r = 0 if diff_r == 0 else (1 if diff_r > 0 else -1)
        step_c = 0 if diff_c == 0 else (1 if diff_c > 0 else -1)
        return self._is_path_clear(board, src, dst, step_r, step_c)

class BishopStrategy(MovementStrategy):
    def is_valid(self, board, src, dst) -> bool:
        if not self._base_target_check(board, src, dst):
            return False
        diff_r, diff_c = dst.row - src.row, dst.col - src.col
        if abs(diff_r) != abs(diff_c):
            return False
        step_r = 1 if diff_r > 0 else -1
        step_c = 1 if diff_c > 0 else -1
        return self._is_path_clear(board, src, dst, step_r, step_c)

class QueenStrategy(MovementStrategy):
    def is_valid(self, board, src, dst) -> bool:
        if not self._base_target_check(board, src, dst):
            return False
        diff_r, diff_c = dst.row - src.row, dst.col - src.col
        if diff_r == 0 or diff_c == 0:
            step_r = 0 if diff_r == 0 else (1 if diff_r > 0 else -1)
            step_c = 0 if diff_c == 0 else (1 if diff_c > 0 else -1)
        elif abs(diff_r) == abs(diff_c):
            step_r = 1 if diff_r > 0 else -1
            step_c = 1 if diff_c > 0 else -1
        else:
            return False
        return self._is_path_clear(board, src, dst, step_r, step_c)

class KnightStrategy(MovementStrategy):
    def is_valid(self, board, src, dst) -> bool:
        # the knight skips over pieces (does not call _is_path_clear), but still subject to target square check
        if not self._base_target_check(board, src, dst):
            return False
        abs_r, abs_c = abs(dst.row - src.row), abs(dst.col - src.col)
        return (abs_r == 1 and abs_c == 2) or (abs_r == 2 and abs_c == 1)

class PawnStrategy(MovementStrategy):
    def is_valid(self, board: list, src: Position, dst: Position) -> bool:
        piece = board[src.row][src.col]
        
        # Determine the direction of movement based on the color of the tool
        # white moves up (negative in rows), black moves down (positive in rows)
        direction = -1 if piece.color == Color.WHITE else 1
        
        diff_r = dst.row - src.row
        diff_c = dst.col - src.col
        
        target_piece = board[dst.row][dst.col]
        
        # 1. One step forward movement
        # Conditions: Column difference is 0, row matches direction, and target slot is completely empty (no forward hit)
        if diff_c == 0 and diff_r == direction:
            return target_piece is None
            
        # 2. hitting on the diagonal
        # Conditions: One square forward in the correct direction, one column away, and the target square contains an enemy piece
        if abs(diff_c) == 1 and diff_r == direction:
            return target_piece is not None and target_piece.color != piece.color

        # Any other move (including attempting to move 2 steps) is illegal
        return False

class StrategyFactory:
    _strategies = {
        PieceType.KING: KingStrategy(), PieceType.QUEEN: QueenStrategy(),
        PieceType.ROOK: RookStrategy(), PieceType.BISHOP: BishopStrategy(),
        PieceType.KNIGHT: KnightStrategy(), PieceType.PAWN: PawnStrategy()
    }

    @classmethod
    def get_strategy(cls, piece_type: PieceType) -> MovementStrategy:
        return cls._strategies.get(piece_type)