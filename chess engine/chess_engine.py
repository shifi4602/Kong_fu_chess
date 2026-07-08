from typing import List, Dict, Optional
from types_and_constants import Color, PieceType, Position, Piece
from validators import (
    MoveValidator, RedirectValidator, CooldownValidator, 
    PieceMovementValidator, ConcurrencyValidator
)

class ChessEngine:
    # Change: update default travel_duration to 1000ms
    def __init__(self, cooldown_duration: int = 5000, travel_duration: int = 1000):
        self.board_matrix: List[List[Optional[Piece]]] = []
        self.cooldown_matrix: List[List[int]] = []
        self.current_time: int = 0
        self.cooldown_duration: int = cooldown_duration
        self.travel_duration: int = travel_duration
        self.selected_pos: Optional[Position] = None
        self._pending_moves: List[Dict] = []
        
        # Inject game rules (Dependency Injection), including the new concurrency rule
        self._validators: List[MoveValidator] = [
            RedirectValidator(),
            CooldownValidator(),
            PieceMovementValidator(),
            ConcurrencyValidator()
        ]

    def add_board_row(self, row_pieces: list):
        self.board_matrix.append(row_pieces)

    def init_cooldown_matrix(self):
        if self.board_matrix:
            self.cooldown_matrix = [[0] * len(self.board_matrix[0]) for _ in range(len(self.board_matrix))]

    def advance_time(self, ms: int):
        self.current_time += ms
        self._update_game_state()

    def _is_piece_moving(self, pos: Position) -> bool:
        for move in self._pending_moves:
            if move['src'] == pos:
                return True
        return False

    def handle_click_position(self, pos: Position):
        num_rows = len(self.board_matrix)
        num_cols = len(self.board_matrix[0]) if num_rows > 0 else 0
        
        if pos.row < 0 or pos.row >= num_rows or pos.col < 0 or pos.col >= num_cols:
            return

        target_piece = self.board_matrix[pos.row][pos.col]

        if self.selected_pos is None:
            if target_piece is not None and not self._is_piece_moving(pos):
                self.selected_pos = pos
        else:
            selected_piece = self.board_matrix[self.selected_pos.row][self.selected_pos.col]
            
            if target_piece is not None and target_piece.color == selected_piece.color:
                if not self._is_piece_moving(pos):
                    self.selected_pos = pos
                else:
                    self.selected_pos = None
            else:
                src = self.selected_pos
                dst = pos
                
                if all(v.validate(self, src, dst) for v in self._validators):
                    arrival_time = self.current_time + self.travel_duration
                    self._pending_moves.append({
                        'src': src,
                        'dst': dst,
                        'piece': selected_piece,
                        'arrival_time': arrival_time
                    })
                    
                    # Electronic lock until the exact arrival time
                    self.cooldown_matrix[dst.row][dst.col] = arrival_time
                    self.cooldown_matrix[src.row][src.col] = 0
                        
                self.selected_pos = None

    def _update_game_state(self):
        still_pending = []
        for move in self._pending_moves:
            # שימוש ב >= מבטיח סנכרון מדויק של זמנים מול ה-VPL
            if self.current_time >= move['arrival_time']:
                src = move['src']
                dst = move['dst']
                piece = move['piece']
                
                self.board_matrix[dst.row][dst.col] = piece
                if self.board_matrix[src.row][src.col] == piece:
                    self.board_matrix[src.row][src.col] = None
            else:
                still_pending.append(move)
        self._pending_moves = still_pending

    def print_current_board(self):
        self._update_game_state()
        for row in self.board_matrix:
            row_str = []
            for cell in row:
                if cell is None:
                    row_str.append(".")
                else:
                    row_str.append(f"{cell.color.value}{cell.piece_type.value}")
            print(" ".join(row_str))