import chess
from find_best_move import find_best_move

def main():
    """Main function to run the chess AI."""

    board = chess.Board()
    depth = 2

    while not board.is_game_over():
        print(board)
        print("\n")

        player_move = input("Enter your move (in UCI format, e.g., e2e4): ")
        try:
            move = chess.Move.from_uci(player_move)
            if move in board.legal_moves:
                board.push(move)
            else:
                print("Invalid move. Please try again.")
                continue
        except ValueError:
            print("Invalid move format. Please use UCI format.")
            continue

        ai_move_result = find_best_move(board, depth)
        if ai_move_result:
            print(f"AI plays: {ai_move_result}")
            board.push(ai_move_result)
        else:
            print("AI cannot make a move.")

    print("Game over!")
    print("Result:", board.result())

if __name__ == "__main__":
    main()
