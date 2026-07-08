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
    tokens = line.strip().split()
    if not tokens:
        return [], 0
    
    row_pieces = []
    for token in tokens:
        if token == '.':
            row_pieces.append(None)
        elif len(token) == 2:
            color_char, type_char = token[0], token[1]
            color = Color(color_char)
            piece_type = PieceType(type_char)
            row_pieces.append(Piece(color, piece_type))
        else:
            raise ValueError(f"Invalid token: {token}")
            
    if expected_width != -1 and len(row_pieces) != expected_width:
        raise ValueError("Inconsistent board width")
    return row_pieces, len(row_pieces)


def parse_board_line(line: str, expected_width: int) -> Tuple[List, int]:
    tokens = line.strip().split()
    if not tokens:
        return [], 0
    
    row_pieces = []
    for token in tokens:
        if token == '.':
            row_pieces.append(None)
        elif len(token) == 2:
            color_char, type_char = token[0], token[1]
            color = Color(color_char)
            piece_type = PieceType(type_char)
            row_pieces.append(Piece(color, piece_type))
        else:
            raise ValueError(f"Invalid token: {token}")
            
    if expected_width != -1 and len(row_pieces) != expected_width:
        raise ValueError("Inconsistent board width")
    return row_pieces, len(row_pieces)


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
            parse_board_line(line, command_queue)


def execute_commands(engine: ChessEngine, command_queue: deque):
    """merges the command queue and executes them on the game engine."""
    while command_queue:
        cmd = command_queue.popleft()
        cmd.execute(engine)

# --- הפונקציה הראשית להרצה ---

def main():
    lines = sys.stdin.read().splitlines()
    engine = ChessEngine()
    command_queue = deque()
    
    mode = "none"
    expected_width = -1
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned == "Board:":
            mode = "board"
            continue
        elif cleaned == "Commands:":
            mode = "commands"
            engine.init_cooldown_matrix()
            continue
            
        if mode == "board":
            row_pieces, w = parse_board_line(cleaned, expected_width)
            if w > 0:
                expected_width = w
                engine.add_board_row(row_pieces)
        elif mode == "commands":
            parse_board_line(cleaned, command_queue)
            
    while command_queue:
        item = command_queue.popleft()
        if item[0] == "click":
            _, x, y = item
            row = y // 100
            col = x // 100
            engine.handle_click_position(Position(row, col))
        elif item[0] == "wait":
            _, ms = item
            engine.advance_time(ms)
        elif item[0] == "print_board":
            engine.print_current_board()