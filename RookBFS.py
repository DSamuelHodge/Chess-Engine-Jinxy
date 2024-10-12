import random
from collections import deque

columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
rows = ['8', '7', '6', '5', '4', '3', '2', '1']
rook_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def is_valid_position(position):
    return len(position) == 2 and position[0] in columns and position[1] in rows

def random_position():
    col = random.choice(columns)
    row = random.choice(rows)
    return f"{col}{row}"

def get_valid_rook_moves(rook_position):
    valid_moves = []
    col_index = columns.index(rook_position[0])
    row_index = rows.index(rook_position[1])

    for direction in rook_directions:
        for step in range(1, 8):  # Allow movement up to 7 squares in any direction
            new_col_index = col_index + direction[0] * step
            new_row_index = row_index + direction[1] * step

            if 0 <= new_col_index < 8 and 0 <= new_row_index < 8:
                new_position = f"{columns[new_col_index]}{rows[new_row_index]}"
                valid_moves.append(new_position)
            else:
                break  # Stop if it goes off the board

    return valid_moves

def bfs_rook_to_king(rook_position, king_position):
    queue = deque([(rook_position, [rook_position])])
    visited = set()

    while queue:
        current_position, path = queue.popleft()

        if current_position == king_position:
            return path

        visited.add(current_position)

        for move in get_valid_rook_moves(current_position):
            if move not in visited:
                queue.append((move, path + [move]))

    return None

def is_valid_king_move(current_king_position, new_king_position):
    col_diff = columns.index(new_king_position[0]) - columns.index(current_king_position[0])
    row_diff = rows.index(new_king_position[1]) - rows.index(current_king_position[1])
    return (col_diff, row_diff) in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

def get_valid_king_moves(king_position, rook_position):
    valid_moves = []
    col_index = columns.index(king_position[0])
    row_index = rows.index(king_position[1])

    for move in [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]:
        new_col_index = col_index + move[0]
        new_row_index = row_index + move[1]

        if 0 <= new_col_index < 8 and 0 <= new_row_index < 8:
            new_position = f"{columns[new_col_index]}{rows[new_row_index]}"
            if new_position not in get_valid_rook_moves(rook_position):
                valid_moves.append(new_position)

    return valid_moves

def rook_turn(rook_position, king_position):
    valid_moves = get_valid_rook_moves(rook_position)

    # Check if we can move to a position that puts the King in check
    check_moves = [move for move in valid_moves if move[0] == king_position[0] or move[1] == king_position[1]]

    if check_moves:
        # Move to the furthest valid check move
        furthest_check_move = max(check_moves, key=lambda m: (columns.index(m[0]) - columns.index(rook_position[0])) ** 2 +
                                                    (rows.index(m[1]) - rows.index(rook_position[1])) ** 2)
        print(f"Rook moves to: {furthest_check_move} and puts King in check!")
        return furthest_check_move

    # If no check moves, move normally towards the King
    path = bfs_rook_to_king(rook_position, king_position)
    if path and len(path) > 1:
        new_rook_position = path[1]
        print(f"Rook moves to: {new_rook_position}")
        return new_rook_position
    
    return rook_position

def king_turn(rook_position, current_king_position):
    valid_moves = get_valid_king_moves(current_king_position, rook_position)
    new_king_position = input(f"Your turn! Enter new King position (e.g., 'e4') avoiding rook at {rook_position}: ").lower()

    while new_king_position not in valid_moves:
        new_king_position = input(f"Invalid move! That square is under the rook's threat or not valid. Pick another position: ").lower()

    return new_king_position

def is_king_in_check(rook_position, king_position):
    return king_position in get_valid_rook_moves(rook_position)

def can_king_capture_rook(rook_position, king_position):
    return rook_position in get_valid_king_moves(king_position, rook_position)

def game_loop():
    rook_position = random_position()
    print(f"Rook starts at {rook_position}")
    king_position = input("Enter the initial position of the King (e.g., 'e4'): ").lower()

    while not is_valid_position(king_position):
        king_position = input("Invalid position! Enter a valid initial position for the King: ").lower()

    print(f"Game start! Rook starts at {rook_position}, King starts at {king_position}")

    while rook_position != king_position:
        rook_position = rook_turn(rook_position, king_position)

        if is_king_in_check(rook_position, king_position):
            print(f"Check! The rook is threatening the King at {king_position}!")

        if can_king_capture_rook(rook_position, king_position):
            print(f"King captured the Rook at {rook_position}! You win!")
            break

        king_position = king_turn(rook_position, king_position)

    if rook_position == king_position:
        print("The rook captured the king! Game over.")

if __name__ == "__main__":
    game_loop()
