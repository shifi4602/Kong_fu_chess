import sys
from collections import deque
from types_and_constants import Color, PieceType, Position, Piece
from chess_engine import ChessEngine
from typing import Tuple, List

# --- Command Pattern ---

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

# --- Parsing & Logic Split ---

def parse_token(token: str) -> Piece:
    """parses a single token into a Piece object or None for empty squares."""
    if token == ".":
        return None
    return Piece(
        color=Color.from_value(token[0]), 
        piece_type=PieceType.from_value(token[1].upper())
    )

def parse_board_line(line: str, expected_width: int) -> Tuple[List, int]:
    """parses a single board line and validates the tokens and row width."""
    tokens = line.split()
    if not tokens:
        return [], expected_width
        
    if expected_width == -1:
        expected_width = len(tokens)
    elif len(tokens) != expected_width:
        print("ERROR ROW_WIDTH_MISMATCH")
        sys.exit(0)
        
    row_pieces = []
    for token in tokens:
        if token != ".":
            if len(token) != 2 or token[0] not in ['w', 'b'] or token[1].upper() not in ['K', 'Q', 'R', 'B', 'N', 'P']:
                print("ERROR UNKNOWN_TOKEN")
                sys.exit(0)
        row_pieces.append(parse_token(token))
        
    return row_pieces, expected_width


def parse_command_line(line: str, command_queue: deque):
    """parses a single command line and adds the appropriate command to the queue."""
    parts = line.split()
    if not parts:
        return

    cmd_type = parts[0].lower()

    if cmd_type == "click" and len(parts) == 3:
        try:
            command_queue.append(ClickCommand(int(parts[1]), int(parts[2])))
        except ValueError:
            pass
    elif cmd_type == "wait" and len(parts) == 2:
        try:
            command_queue.append(WaitCommand(int(parts[1])))
        except ValueError:
            pass
    elif line == "print board":
        command_queue.append(PrintBoardCommand())


def read_input_and_build_state(engine: ChessEngine, command_queue: deque):
    """reads the input and navigates between reading the board and reading commands."""
    current_mode = None
    expected_width = -1

    for line in sys.stdin:
        line = line.strip()
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
            row_pieces, expected_width = parse_board_line(line, expected_width)
            if row_pieces:
                engine.add_board_row(row_pieces)
        elif current_mode == "commands":
            parse_command_line(line, command_queue)


def execute_commands(engine: ChessEngine, command_queue: deque):
    """merges the command queue and executes them on the game engine."""
    while command_queue:
        cmd = command_queue.popleft()
        cmd.execute(engine)

# --- הפונקציה הראשית להרצה ---

def main():
    # אתחול המנוע עם Cooldown של 5000ms וזמן נסיעה של 2000ms בהתאם לעדכון האחרון
    engine = ChessEngine(cooldown_duration=5000, travel_duration=2000)
    command_queue = deque()
    
    # שלב 1: עיבוד וקריאת זרם הקלט (לוח ופקודות)
    read_input_and_build_state(engine, command_queue)
    
    # שלב 2: הרצת כל הפקודות על הלוח לפי סדר קבלתן
    execute_commands(engine, command_queue)


if __name__ == "__main__":
    main()