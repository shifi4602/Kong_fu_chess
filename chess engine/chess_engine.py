from types_and_constants import Color, PieceType, Position, Piece
from movement_strategies import StrategyFactory

class ChessEngine:
    def __init__(self, cooldown_duration: int = 5000, travel_duration: int = 2000):
        self.board_matrix = []
        self.cooldown_matrix = []
        self.current_time = 0
        self.cooldown_duration = cooldown_duration
        self.travel_duration = travel_duration # time it takes for a piece to "travel" to its new position
        self.selected_pos = None
        self._pending_moves = [] # A queue for the moves that are pending

    def add_board_row(self, row_pieces: list):
        self.board_matrix.append(row_pieces)

    def init_cooldown_matrix(self):
        if self.board_matrix:
            self.cooldown_matrix = [[0] * len(self.board_matrix[0]) for _ in range(len(self.board_matrix))]

    def advance_time(self, ms: int):
        self.current_time += ms
        # Update the board status immediately with the time advancement.
        self._update_game_state()

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
                        
                        # write the move to the pending moves queue instead of updating the board immediately
                        arrival_time = self.current_time + self.travel_duration
                        self._pending_moves.append({
                            'src': self.selected_pos,
                            'dst': pos,
                            'piece': selected_piece,
                            'arrival_time': arrival_time
                        })
                        
                        # Cooldowns are updated immediately upon departure
                        self.cooldown_matrix[pos.row][pos.col] = arrival_time + self.cooldown_duration
                        self.cooldown_matrix[self.selected_pos.row][self.selected_pos.col] = 0
                        
                self.selected_pos = None

    def _update_game_state(self):
        """Scanning and executing moves whose arrival time has arrived (Lazy Evaluation)."""
        still_pending = []
        for move in self._pending_moves:
            if self.current_time >= move['arrival_time']:
                src = move['src']
                dst = move['dst']
                piece = move['piece']
                
                # Apply the physical change to the board
                self.board_matrix[dst.row][dst.col] = piece
                # Delete from the source slot only if the tool is still there and hasn't moved again in the meantime
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