import sys

# Defining constants outside the function prevents re-creation in memory on each run (saves processing time)
VALID_COLORS = {'w', 'b'}
VALID_PIECES = {'K', 'Q', 'R', 'B', 'N', 'P'}

def is_valid_token(token):
    """Check if the current token is valid (empty square or recognized piece)."""
    if token == ".":
        return True
    return len(token) == 2 and token[0] in VALID_COLORS and token[1] in VALID_PIECES

def process_board_line(line, board_matrix, expected_width):
    """Process a board line, checking dimensions and tokens, and updating the matrix."""
    tokens = line.split()
    if not tokens:
        return expected_width, True
        
    # 1. Dimension validation (row width)
    if expected_width == -1:
        expected_width = len(tokens)
    elif len(tokens) != expected_width:
        print("ERROR ROW_WIDTH_MISMATCH")
        return expected_width, False
        
    # 2. Token validation
    for token in tokens:
        if not is_valid_token(token):
            print("ERROR UNKNOWN_TOKEN")
            return expected_width, False
            
    board_matrix.append(tokens)
    return expected_width, True

def execute_command(line, board_matrix):
    """Decodes and executes the commands received from the input."""
    if line == "print board":
        output = "\n".join(" ".join(row) for row in board_matrix)
        print(output)

def main():
    # Read all lines from standard input and clean up unnecessary spaces
    lines = [line.strip() for line in sys.stdin]
    
    board_matrix = []
    current_mode = None  # can be 'board' or 'commands'
    expected_width = -1
    
    for line in lines:
        if not line:
            continue

        # Detecting a change in input mode    
        if line == "Board:":
            current_mode = "board"
            continue
        elif line == "Commands:":
            current_mode = "commands"
            continue
            
        # Navigation of the logic to the appropriate function based on the mode
        if current_mode == "board":
            expected_width, success = process_board_line(line, board_matrix, expected_width)
            if not success:
                return  # Exit the program in case of a validation error
                
        elif current_mode == "commands":
            execute_command(line, board_matrix)

if __name__ == "__main__":
    main()