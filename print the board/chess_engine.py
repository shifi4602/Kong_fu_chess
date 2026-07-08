import sys

VALID_COLORS = {'w', 'b'}
VALID_PIECES = {'K', 'Q', 'R', 'B', 'N', 'P'}

def is_valid_token(token):
    """Check if the current token is valid (empty square or recognized piece)."""
    if token == ".":
        return True
    return len(token) == 2 and token[0] in VALID_COLORS and token[1] in VALID_PIECES

def is_valid_chess_move(board, src, dst):
    """
    Check the legality of a chess piece move based on the piece type and board interval.
    Returns True if the move is legal, otherwise False.
    """
    sr, sc = src
    dr, dc = dst
    piece = board[sr][sc]
    
    if sr == dr and sc == dc:
        return False
        
    color = piece[0]
    ptype = piece[1]
    
    # invalid move if the destination is occupied by a piece of the same color
    if board[dr][dc] != '.' and board[dr][dc][0] == color:
        return False
        
    diff_r = dr - sr
    diff_c = dc - sc
    abs_r = abs(diff_r)
    abs_c = abs(diff_c)
    
    # מלך (King)
    if ptype == 'K':
        return abs_r <= 1 and abs_c <= 1
        
    # צריח (Rook)
    elif ptype == 'R':
        if diff_r != 0 and diff_c != 0:
            return False
        step_r = 0 if diff_r == 0 else (1 if diff_r > 0 else -1)
        step_c = 0 if diff_c == 0 else (1 if diff_c > 0 else -1)
        curr_r, curr_c = sr + step_r, sc + step_c
        while (curr_r, curr_c) != (dr, dc):
            if board[curr_r][curr_c] != '.':
                return False
            curr_r += step_r
            curr_c += step_c
        return True
        
    # רץ (Bishop)
    elif ptype == 'B':
        if abs_r != abs_c:
            return False
        step_r = 1 if diff_r > 0 else -1
        step_c = 1 if diff_c > 0 else -1
        curr_r, curr_c = sr + step_r, sc + step_c
        while (curr_r, curr_c) != (dr, dc):
            if board[curr_r][curr_c] != '.':
                return False
            curr_r += step_r
            curr_c += step_c
        return True
        
    # מלכה (Queen)
    elif ptype == 'Q':
        if diff_r == 0 or diff_c == 0:
            step_r = 0 if diff_r == 0 else (1 if diff_r > 0 else -1)
            step_c = 0 if diff_c == 0 else (1 if diff_c > 0 else -1)
        elif abs_r == abs_c:
            step_r = 1 if diff_r > 0 else -1
            step_c = 1 if diff_c > 0 else -1
        else:
            return False
        curr_r, curr_c = sr + step_r, sc + step_c
        while (curr_r, curr_c) != (dr, dc):
            if board[curr_r][curr_c] != '.':
                return False
            curr_r += step_r
            curr_c += step_c
        return True
        
    # פרש (Knight)
    elif ptype == 'N':
        return (abs_r == 1 and abs_c == 2) or (abs_r == 2 and abs_c == 1)
        
    # רגלי (Pawn)
    elif ptype == 'P':
        direction = -1 if color == 'w' else 1
        # one step forward
        if diff_c == 0 and diff_r == direction and board[dr][dc] == '.':
            return True
        # two steps forward from the initial row
        init_row = len(board) - 2 if color == 'w' else 1
        if diff_c == 0 and diff_r == 2 * direction and sr == init_row:
            if board[sr + direction][sc] == '.' and board[dr][dc] == '.':
                return True
        # capture diagonally
        if abs_c == 1 and diff_r == direction and board[dr][dc] != '.' and board[dr][dc][0] != color:
            return True
        return False
        
    return False

def main():
    # Read all lines from standard input and clean up unnecessary spaces
    lines = [line.strip() for line in sys.stdin]
    
    board_matrix = []
    current_mode = None  # can be 'board' or 'commands'
    expected_width = -1
    
    # State management variables for the game
    selected_pos = None
    current_time = 0
    cooldown_duration = 5000  # default cooldown duration for pieces (5 seconds)
    cooldown_matrix = []

    for line in lines:
        if not line:
            continue

        #recognizing a change in input mode
        if line == "Board:":
            current_mode = "board"
            continue
        elif line == "Commands:":
            current_mode = "commands"
            
            # initialize the cooldown matrix once the board size is known and fully scanned
            num_rows = len(board_matrix)
            if num_rows > 0:
                num_cols = len(board_matrix[0])
                cooldown_matrix = [[0] * num_cols for _ in range(num_rows)]
            continue

        # 1. Processing the board and validations (tests 5 and 6)    
        if current_mode == "board":
            tokens = line.split()
            if not tokens:
                continue
            if expected_width == -1:
                expected_width = len(tokens)
            elif len(tokens) != expected_width:
                print("ERROR ROW_WIDTH_MISMATCH")
                return  # exit immediately without printing the board
                
            for token in tokens:
                if not is_valid_token(token):
                    print("ERROR UNKNOWN_TOKEN")
                    return  # exit immediately without printing the board
            board_matrix.append(tokens)
            
        # 2. Processing commands in real-time (tests 1 to 4)
        elif current_mode == "commands":
            parts = line.split()
            if not parts:
                continue
                
            cmd_type = parts[0].lower()
            
            if cmd_type == "click" and len(parts) == 3:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                except ValueError:
                    continue
                    
                num_rows = len(board_matrix)
                num_cols = len(board_matrix[0]) if num_rows > 0 else 0
                
                # Translation of pixel coordinates to matrix indices
                col = x // 100
                row = y // 100
                
                # Test 3: clicking outside the dynamic board boundaries is ignored
                if row < 0 or row >= num_rows or col < 0 or col >= num_cols:
                    continue
                    
                token = board_matrix[row][col]
                
                #State 1: there is no currently selected piece
                if selected_pos is None:
                    if token != ".":
                        # Test 1: clicking on a piece selects it
                        selected_pos = (row, col)
                    # Test 2: click on an empty square without a previous selection is ignored (no action taken)
                
                # State 2: there is already a selected piece in the system
                else:
                    sel_row, sel_col = selected_pos
                    sel_token = board_matrix[sel_row][sel_col]
                    
                    if token != "." and token[0] == sel_token[0]:

                        # Test 4: click on another friendly piece replaces the selection
                        selected_pos = (row, col)
                    else:
                        # try to move to an empty square or capture an enemy piece
                        if current_time >= cooldown_matrix[sel_row][sel_col]:
                            if is_valid_chess_move(board_matrix, selected_pos, (row, col)):
                                # Making the move and updating the board                                #
                                board_matrix[row][col] = sel_token
                                board_matrix[sel_row][sel_col] = "."
                                # Apply the cooldown mechanism to the new location
                                cooldown_matrix[row][col] = current_time + cooldown_duration
                                cooldown_matrix[sel_row][sel_col] = 0
                        # Reset the selection after sending a traffic request (whether successful or failed)
                        selected_pos = None
                        
            elif cmd_type == "wait" and len(parts) == 2:
                try:
                    ms = int(parts[1])
                    current_time += ms
                except ValueError:
                    continue
                    
            elif line == "print board":
                for row in board_matrix:
                    print(" ".join(row))

if __name__ == "__main__":
    main()