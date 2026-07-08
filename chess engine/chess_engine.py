from types_and_constants import Color, PieceType, Position, Piece
from movement_strategies import StrategyFactory

class ChessEngine:
    def __init__(self, cooldown_duration: int = 5000):
        self.board_matrix = []
        self.cooldown_matrix = []
        self.current_time = 0
        self.cooldown_duration = cooldown_duration
        self.selected_pos = None

    def add_board_row(self, row_pieces: list):
        self.board_matrix.append(row_pieces)

    def init_cooldown_matrix(self):
        if self.board_matrix:
            self.cooldown_matrix = [[0] * len(self.board_matrix[0]) for _ in range(len(self.board_matrix))]

    def advance_time(self, ms: int):
        self.current_time += ms

    def handle_click_position(self, pos: Position):
        num_rows = len(self.board_matrix)
        num_cols = len(self.board_matrix[0]) if num_rows > 0 else 0
        
        if pos.row < 0 or pos.row >= num_rows or pos.col < 0 or pos.col >= num_cols:
            return

        target_piece = self.board_matrix[pos.row][pos.col]

        if self.selected_pos is None:
            if target_piece is not None:
                self.selected_pos = pos
        else:
            selected_piece = self.board_matrix[self.selected_pos.row][self.selected_pos.col]
            
            if target_piece is not None and target_piece.color == selected_piece.color:
                self.selected_pos = pos
            else:
                if self.current_time >= self.cooldown_matrix[self.selected_pos.row][self.selected_pos.col]:
                    strategy = StrategyFactory.get_strategy(selected_piece.piece_type)
                    if strategy and strategy.is_valid(self.board_matrix, self.selected_pos, pos):
                        self.board_matrix[pos.row][pos.col] = selected_piece
                        self.board_matrix[self.selected_pos.row][self.selected_pos.col] = None
                        self.cooldown_matrix[pos.row][pos.col] = self.current_time + self.cooldown_duration
                        self.cooldown_matrix[self.selected_pos.row][self.selected_pos.col] = 0
                self.selected_pos = None

    def print_current_board(self):
        for row in self.board_matrix:
            row_str = []
            for cell in row:
                if cell is None:
                    row_str.append(".")
                else:
                    row_str.append(f"{cell.color.value}{cell.piece_type.value}")
            print(" ".join(row_str))