from kungfu_chess.model import Board, Color, PieceKind, Position


class BoardPrinter:
    _COLOR_CHAR = {
        Color.WHITE: 'w',
        Color.BLACK: 'b',
    }
    _KIND_CHAR = {
        PieceKind.KING:   'K',
        PieceKind.QUEEN:  'Q',
        PieceKind.ROOK:   'R',
        PieceKind.BISHOP: 'B',
        PieceKind.KNIGHT: 'N',
        PieceKind.PAWN:   'P',
    }

    def render(self, board: Board) -> str:
        row_strings = []
        for row in range(board.rows):
            tokens = []
            for col in range(board.cols):
                piece = board.get(Position(row, col))
                if piece is None:
                    tokens.append('.')
                else:
                    color_char = self._COLOR_CHAR[piece.color]
                    kind_char = self._KIND_CHAR[piece.kind]
                    tokens.append(color_char + kind_char)
            row_strings.append(' '.join(tokens))
        return '\n'.join(row_strings)
