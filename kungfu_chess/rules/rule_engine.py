from abc import ABC, abstractmethod
from typing import Dict, List

from kungfu_chess.model import GameState, PieceKind, PieceState
from .move_request import MoveRequest
from .piece_rules import PieceRule, KingRule, QueenRule, RookRule, BishopRule, KnightRule, PawnRule


class MoveValidator(ABC):
    @abstractmethod
    def validate(self, state: GameState, request: MoveRequest) -> bool:
        pass


class PieceExistsValidator(MoveValidator):
    def validate(self, state: GameState, request: MoveRequest) -> bool:
        if state.board.get(request.src) is None:
            return False
        return True


class PieceIdleValidator(MoveValidator):
    def validate(self, state: GameState, request: MoveRequest) -> bool:
        piece = state.board.get(request.src)
        if piece is None:
            return False
        if piece.state != PieceState.IDLE:
            return False
        return True


class DestinationValidator(MoveValidator):
    def validate(self, state: GameState, request: MoveRequest) -> bool:
        board = state.board
        dst = request.dst
        if not board.in_bounds(dst):
            return False
        occupant = board.get(dst)
        if occupant is None:
            return True
        moving_piece = board.get(request.src)
        if occupant.color == moving_piece.color:
            return False
        return True


class MovementValidator(MoveValidator):
    def __init__(self, rules: Dict[PieceKind, PieceRule]) -> None:
        self._rules = rules

    def validate(self, state: GameState, request: MoveRequest) -> bool:
        piece = state.board.get(request.src)
        if piece is None:
            return False
        rule = self._rules.get(piece.kind)
        if rule is None:
            return False
        if not rule.can_move(state.board, request):
            return False
        return True


class RuleEngine:
    def __init__(self, validators: List[MoveValidator]) -> None:
        self._validators = validators

    def can_move(self, state: GameState, request: MoveRequest) -> bool:
        for validator in self._validators:
            if not validator.validate(state, request):
                return False
        return True


def default_rule_engine() -> RuleEngine:
    rules: Dict[PieceKind, PieceRule] = {
        PieceKind.KING:   KingRule(),
        PieceKind.QUEEN:  QueenRule(),
        PieceKind.ROOK:   RookRule(),
        PieceKind.BISHOP: BishopRule(),
        PieceKind.KNIGHT: KnightRule(),
        PieceKind.PAWN:   PawnRule(),
    }
    validators: List[MoveValidator] = [
        PieceExistsValidator(),
        PieceIdleValidator(),
        DestinationValidator(),
        MovementValidator(rules),
    ]
    return RuleEngine(validators)
