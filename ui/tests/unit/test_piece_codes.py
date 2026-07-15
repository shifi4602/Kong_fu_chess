from kungfu_chess.model import Color, PieceKind
from ui.assets.piece_codes import piece_code


def test_maps_every_color_kind_combination_to_the_expected_code():
    expected = {
        (Color.WHITE, PieceKind.KING): "wK",
        (Color.WHITE, PieceKind.QUEEN): "wQ",
        (Color.WHITE, PieceKind.ROOK): "wR",
        (Color.WHITE, PieceKind.BISHOP): "wB",
        (Color.WHITE, PieceKind.KNIGHT): "wN",
        (Color.WHITE, PieceKind.PAWN): "wP",
        (Color.BLACK, PieceKind.KING): "bK",
        (Color.BLACK, PieceKind.QUEEN): "bQ",
        (Color.BLACK, PieceKind.ROOK): "bR",
        (Color.BLACK, PieceKind.BISHOP): "bB",
        (Color.BLACK, PieceKind.KNIGHT): "bN",
        (Color.BLACK, PieceKind.PAWN): "bP",
    }
    for (color, kind), code in expected.items():
        assert piece_code(color, kind) == code


def test_codes_are_unique_across_all_combinations():
    codes = {piece_code(color, kind) for color in Color for kind in PieceKind}
    assert len(codes) == len(Color) * len(PieceKind)
