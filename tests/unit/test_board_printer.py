from kungfu_chess.io.board_parser import BoardParser
from kungfu_chess.io.board_printer import BoardPrinter
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Color, Piece, PieceKind
from kungfu_chess.model.position import Position


def test_render_single_piece():
    board = Board(2, 2)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(0, 0))
    board.place(wk, Position(0, 0))
    printer = BoardPrinter()
    assert printer.render(board) == "wK .\n. ."


def test_render_empty_board():
    board = Board(2, 2)
    printer = BoardPrinter()
    assert printer.render(board) == ". .\n. ."


def test_render_two_pieces():
    board = Board(2, 2)
    wk = Piece(id='wK', color=Color.WHITE, kind=PieceKind.KING, cell=Position(0, 0))
    bk = Piece(id='bK', color=Color.BLACK, kind=PieceKind.KING, cell=Position(1, 1))
    board.place(wk, Position(0, 0))
    board.place(bk, Position(1, 1))
    printer = BoardPrinter()
    assert printer.render(board) == "wK .\n. bK"


def test_roundtrip():
    text = "wK .\n. bK"
    parser = BoardParser()
    printer = BoardPrinter()
    board = parser.parse(text)
    rendered = printer.render(board)
    assert rendered == text


def test_roundtrip_full_row():
    text = "wK wQ wR wB wN wP"
    parser = BoardParser()
    printer = BoardPrinter()
    board = parser.parse(text)
    rendered = printer.render(board)
    assert rendered == text


def test_render_all_piece_kinds():
    board = Board(1, 6)
    pieces = [
        (PieceKind.KING,   'wK'),
        (PieceKind.QUEEN,  'wQ'),
        (PieceKind.ROOK,   'wR'),
        (PieceKind.BISHOP, 'wB'),
        (PieceKind.KNIGHT, 'wN'),
        (PieceKind.PAWN,   'wP'),
    ]
    for i, (kind, _) in enumerate(pieces):
        p = Piece(id=f'p{i}', color=Color.WHITE, kind=kind, cell=Position(0, i))
        board.place(p, Position(0, i))
    printer = BoardPrinter()
    result = printer.render(board)
    assert result == "wK wQ wR wB wN wP"


def test_render_black_pieces():
    board = Board(1, 2)
    br = Piece(id='bR', color=Color.BLACK, kind=PieceKind.ROOK, cell=Position(0, 0))
    bb = Piece(id='bB', color=Color.BLACK, kind=PieceKind.BISHOP, cell=Position(0, 1))
    board.place(br, Position(0, 0))
    board.place(bb, Position(0, 1))
    printer = BoardPrinter()
    assert printer.render(board) == "bR bB"
