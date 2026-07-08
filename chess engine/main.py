import sys
from collections import deque
from types_and_constants import Color, PieceType, Position, Piece
from chess_engine import ChessEngine

class Command:
    def execute(self, engine: ChessEngine):
        pass

class ClickCommand(Command):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def execute(self, engine: ChessEngine):
        pos = Position(row=self.y // 100, col=self.x // 100)
        engine.handle_click_position(pos)

class WaitCommand(Command):
    def __init__(self, ms: int):
        self.ms = ms

    def execute(self, engine: ChessEngine):
        engine.advance_time(self.ms)

class PrintBoardCommand(Command):
    def execute(self, engine: ChessEngine):
        engine.print_current_board()

def parse_token(token: str) -> Piece:
    if token == ".":
        return None
    return Piece(
        color=Color.from_value(token[0]), 
        piece_type=PieceType.from_value(token[1].upper())
    )

def main():
    lines = [line.strip() for line in sys.stdin]
    engine = ChessEngine()
    command_queue = deque()
    current_mode = None
    expected_width = -1

    for line in lines:
        if not line:
            continue

        if line == "Board:":
            current_mode = "board"
            continue
        elif line == "Commands:":
            current_mode = "commands"
            engine.init_cooldown_matrix()
            continue

        if current_mode == "board":
            tokens = line.split()
            if not tokens:
                continue
            if expected_width == -1:
                expected_width = len(tokens)
            elif len(tokens) != expected_width:
                print("ERROR ROW_WIDTH_MISMATCH")
                return
                
            row_pieces = []
            for token in tokens:
                if token != ".":
                    if len(token) != 2 or token[0] not in ['w', 'b'] or token[1].upper() not in ['K', 'Q', 'R', 'B', 'N', 'P']:
                        print("ERROR UNKNOWN_TOKEN")
                        return
                row_pieces.append(parse_token(token))
            engine.add_board_row(row_pieces)

        elif current_mode == "commands":
            parts = line.split()
            if not parts:
                continue
            cmd_type = parts[0].lower()

            if cmd_type == "click" and len(parts) == 3:
                try:
                    command_queue.append(ClickCommand(int(parts[1]), int(parts[2])))
                except ValueError:
                    continue
            elif cmd_type == "wait" and len(parts) == 2:
                try:
                    command_queue.append(WaitCommand(int(parts[1])))
                except ValueError:
                    continue
            elif line == "print board":
                command_queue.append(PrintBoardCommand())

    while command_queue:
        cmd = command_queue.popleft()
        cmd.execute(engine)

if __name__ == "__main__":
    main()