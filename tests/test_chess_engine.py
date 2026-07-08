import pytest
from chess_engine import ChessEngine
from types_and_constants import Color, PieceType, Position, Piece

@pytest.fixture
def engine():
    # Initialize with short timings for tests
    eng = ChessEngine(cooldown_duration=100, travel_duration=50)
    eng.add_board_row([Piece(Color.WHITE, PieceType.KING), None])
    eng.add_board_row([None, Piece(Color.BLACK, PieceType.KING)])
    eng.init_cooldown_matrix()
    return eng

# --- Your original tests (adjusted for pytest and new timings) ---

def test_click_out_of_bounds_is_ignored(engine):
    engine.handle_click_position(Position(-1, 0))
    engine.handle_click_position(Position(5, 5))
    assert engine.selected_pos is None
    assert engine.board_matrix[0][0].piece_type == PieceType.KING

def test_selecting_a_piece_sets_selection(engine):
    engine.handle_click_position(Position(0, 0))
    assert engine.selected_pos == Position(0, 0)

def test_clicking_an_empty_square_without_selection_does_nothing(engine):
    engine.handle_click_position(Position(1, 0))
    assert engine.selected_pos is None

def test_valid_move_updates_board_and_clears_selection(engine):
    engine.handle_click_position(Position(0, 0))
    engine.handle_click_position(Position(0, 1))
    
    # In the new mechanism, the piece enters a waiting state
    assert engine.selected_pos is None
    
    # Advance time so the move completes on the board (travel_duration = 50)
    engine.advance_time(50)
    assert engine.board_matrix[0][0] is None
    assert engine.board_matrix[0][1].color == Color.WHITE
    assert engine.board_matrix[0][1].piece_type == PieceType.KING

def test_same_color_piece_switches_selection(engine):
    engine.board_matrix[0][1] = Piece(Color.WHITE, PieceType.PAWN)
    engine.handle_click_position(Position(0, 0))
    engine.handle_click_position(Position(0, 1))
    assert engine.selected_pos == Position(0, 1)

def test_illegal_move_clears_selection_without_mutating_board(engine):
    engine.handle_click_position(Position(0, 0))
    engine.handle_click_position(Position(1, 1))
    assert engine.selected_pos is None
    # The king does not move in this diagonal way, so it stays in place
    assert engine.board_matrix[0][0] is not None

def test_cooldown_prevents_immediate_repeated_move(engine):
    engine.handle_click_position(Position(0, 0))
    engine.handle_click_position(Position(0, 1))
    engine.advance_time(50) # The piece arrived, but it is still under cooldown
    
    # Attempt to move it back immediately
    engine.handle_click_position(Position(0, 1))
    engine.handle_click_position(Position(0, 0))
    
    # The second move should not execute
    engine.advance_time(50)
    assert engine.board_matrix[0][0] is None
    assert engine.board_matrix[0][1] is not None

def test_cooldown_expires_and_move_succeeds(engine):
    engine.handle_click_position(Position(0, 0))
    engine.handle_click_position(Position(0, 1))
    
    # Travel time (50) + cooldown (100) = 150ms
    engine.advance_time(155)
    
    engine.handle_click_position(Position(0, 1))
    engine.handle_click_position(Position(0, 0))
    
    engine.advance_time(50) # Travel time for the second move
    assert engine.board_matrix[0][0] is not None
    assert engine.board_matrix[0][1] is None

def test_init_cooldown_matrix_and_print_board_are_supported(capsys):
    engine = ChessEngine(cooldown_duration=50)
    engine.add_board_row([Piece(Color.WHITE, PieceType.KING), None])
    engine.init_cooldown_matrix()
    
    assert engine.cooldown_matrix == [[0, 0]]
    engine.print_current_board()
    captured = capsys.readouterr()
    assert captured.out.strip() == "wK ."

# --- New tests to complete 100% coverage and edge cases ---

def test_init_cooldown_matrix_empty_board():
    engine = ChessEngine()
    engine.init_cooldown_matrix()
    assert engine.cooldown_matrix == []

def test_handle_click_empty_row_matrix():
    engine = ChessEngine()
    engine.handle_click_position(Position(0, 0))
    assert engine.selected_pos is None

def test_source_cleanup_skipped_if_piece_moved_meanwhile(engine):
    engine.handle_click_position(Position(0, 0))
    engine.handle_click_position(Position(0, 1))
    # Replace the piece at the source while the original piece is in transit
    engine.board_matrix[0][0] = Piece(Color.WHITE, PieceType.PAWN)
    engine.advance_time(50)
    # The source square should not be cleared to None
    assert engine.board_matrix[0][0] == Piece(Color.WHITE, PieceType.PAWN)