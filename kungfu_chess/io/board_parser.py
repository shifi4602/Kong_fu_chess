from kungfu_chess.model import Board, Color, Piece, PieceKind, Position


class BoardParser:
    _COLOR = {
        'w': Color.WHITE,
        'b': Color.BLACK,
    }
    _KIND = {
        'K': PieceKind.KING,
        'Q': PieceKind.QUEEN,
        'R': PieceKind.ROOK,
        'B': PieceKind.BISHOP,
        'N': PieceKind.KNIGHT,
        'P': PieceKind.PAWN,
    }

    def parse(self, text: str) -> Board:
        lines = []
        for raw in text.strip().splitlines():
            stripped = raw.strip()
            if stripped:
                lines.append(stripped)

        if not lines:
            raise ValueError("Board text is empty")

        cols = len(lines[0].split())
        if cols == 0:
            raise ValueError("First row has no tokens")

        board = Board(rows=len(lines), cols=cols)

        for row_idx, line in enumerate(lines):
            tokens = line.split()
            if len(tokens) != cols:
                raise ValueError(
                    f"Row {row_idx} has {len(tokens)} tokens, expected {cols}"
                )
            for col_idx, token in enumerate(tokens):
                if token == '.':
                    continue
                piece = self._parse_token(token, row_idx, col_idx)
                board.place(piece, Position(row_idx, col_idx))

        return board

    def _parse_token(self, token: str, row: int, col: int) -> Piece:
        if len(token) != 2:
            raise ValueError(
                f"Token '{token}' at ({row},{col}) must be exactly 2 characters"
            )
        color_char = token[0]
        kind_char = token[1]

        if color_char not in self._COLOR:
            raise ValueError(
                f"Unknown color '{color_char}' in token '{token}' at ({row},{col})"
            )
        if kind_char not in self._KIND:
            raise ValueError(
                f"Unknown kind '{kind_char}' in token '{token}' at ({row},{col})"
            )

        piece_id = f"{token}{row}{col}"
        return Piece(
            id=piece_id,
            color=self._COLOR[color_char],
            kind=self._KIND[kind_char],
            cell=Position(row, col),
        )
