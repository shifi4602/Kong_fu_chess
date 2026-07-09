from abc import ABC, abstractmethod

from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Color
from kungfu_chess.model.position import Position
from .move_request import MoveRequest


def _is_path_clear(board: Board, src: Position, dst: Position, dr: int, dc: int) -> bool:
    r, c = src.row + dr, src.col + dc
    while (r, c) != (dst.row, dst.col):
        if board.is_occupied(Position(r, c)):
            return False
        r += dr
        c += dc
    return True


class PieceRule(ABC):
    @abstractmethod
    def can_move(self, board: Board, request: MoveRequest) -> bool:
        pass


class KingRule(PieceRule):
    def can_move(self, board: Board, request: MoveRequest) -> bool:
        src, dst = request.src, request.dst
        dr = abs(dst.row - src.row)
        dc = abs(dst.col - src.col)
        if (dr, dc) == (0, 0):
            return False
        if dr > 1 or dc > 1:
            return False
        return True


class RookRule(PieceRule):
    def can_move(self, board: Board, request: MoveRequest) -> bool:
        src, dst = request.src, request.dst
        diff_r = dst.row - src.row
        diff_c = dst.col - src.col
        if diff_r == 0 and diff_c == 0:
            return False
        if diff_r != 0 and diff_c != 0:
            return False
        dr = 0 if diff_r == 0 else (1 if diff_r > 0 else -1)
        dc = 0 if diff_c == 0 else (1 if diff_c > 0 else -1)
        if not _is_path_clear(board, src, dst, dr, dc):
            return False
        return True


class BishopRule(PieceRule):
    def can_move(self, board: Board, request: MoveRequest) -> bool:
        src, dst = request.src, request.dst
        diff_r = dst.row - src.row
        diff_c = dst.col - src.col
        if diff_r == 0:
            return False
        if abs(diff_r) != abs(diff_c):
            return False
        dr = 1 if diff_r > 0 else -1
        dc = 1 if diff_c > 0 else -1
        if not _is_path_clear(board, src, dst, dr, dc):
            return False
        return True


class QueenRule(PieceRule):
    def __init__(self) -> None:
        self._rook = RookRule()
        self._bishop = BishopRule()

    def can_move(self, board: Board, request: MoveRequest) -> bool:
        if self._rook.can_move(board, request):
            return True
        if self._bishop.can_move(board, request):
            return True
        return False


class KnightRule(PieceRule):
    def can_move(self, board: Board, request: MoveRequest) -> bool:
        src, dst = request.src, request.dst
        dr = abs(dst.row - src.row)
        dc = abs(dst.col - src.col)
        if (dr == 2 and dc == 1) or (dr == 1 and dc == 2):
            return True
        return False


class PawnRule(PieceRule):
    def can_move(self, board: Board, request: MoveRequest) -> bool:
        src, dst = request.src, request.dst
        piece = board.get(src)
        if piece is None:
            return False
        direction = -1 if piece.color == Color.WHITE else 1
        diff_r = dst.row - src.row
        diff_c = dst.col - src.col
        if diff_c == 0 and diff_r == direction:
            if board.is_occupied(dst):
                return False
            return True
        if abs(diff_c) == 1 and diff_r == direction:
            target = board.get(dst)
            if target is None:
                return False
            if target.color == piece.color:
                return False
            return True
        return False
