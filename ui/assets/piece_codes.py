from __future__ import annotations

from kungfu_chess.model import Color, PieceKind

_COLOR_LETTER = {
    Color.WHITE: "w",
    Color.BLACK: "b",
}

_KIND_LETTER = {
    PieceKind.KING: "K",
    PieceKind.QUEEN: "Q",
    PieceKind.ROOK: "R",
    PieceKind.BISHOP: "B",
    PieceKind.KNIGHT: "N",
    PieceKind.PAWN: "P",
}


def piece_code(color: Color, kind: PieceKind) -> str:
    """(color, kind) -> the asset folder code under ui/assets/pieces_mine,
    e.g. (WHITE, PAWN) -> "wP". Matches the engine's own board-text token
    order (color letter then kind letter), which is how these assets are
    actually laid out on disk.
    """
    return _COLOR_LETTER[color] + _KIND_LETTER[kind]
