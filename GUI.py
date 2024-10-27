import json
import pygame
import sys
import os
from board import Board, Move, square_to_algebraic
from utils import algebraic_to_square
import random
from minimax import find_best_move

pygame.init()

WIDTH, HEIGHT = 600, 600
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
PIECE_SCALE = 0.6

WHITE_COLOR = (245, 245, 220)
BLACK_COLOR = (139, 69, 19)
TRANSPARENT_GREEN = (0, 255, 0, 100)
TRANSPARENT_BLUE = (0, 0, 255, 100)
TRANSPARENT_RED = (255, 0, 0, 150)

FONT = pygame.font.SysFont('Arial', 36)

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Chess AI')

def load_images():
    images = {}
    pieces = [
        'white_pawn-removebg-preview', 'white_knight-removebg-preview',
        'white_bishop-removebg-preview', 'white_rook-removebg-preview',
        'white_queen-removebg-preview', 'white_king-removebg-preview',
        'black_pawn-removebg-preview', 'black_knight-removebg-preview',
        'black_bishop-removebg-preview', 'black_rook-removebg-preview',
        'black_queen-removebg-preview', 'black_king-removebg-preview'
    ]
    for piece_name in pieces:
        filename = f"{piece_name}.png"
        filepath = os.path.join('images', filename)
        try:
            image = pygame.image.load(filepath)
            image = pygame.transform.scale(image, (int(SQUARE_SIZE * PIECE_SCALE), int(SQUARE_SIZE * PIECE_SCALE)))
            if 'white' in piece_name:
                color = 'w'
            else:
                color = 'b'
            piece_type = piece_name.split('_')[1]
            if 'pawn' in piece_type:
                key = 'P' if color == 'w' else 'p'
            elif 'knight' in piece_type:
                key = 'N' if color == 'w' else 'n'
            elif 'bishop' in piece_type:
                key = 'B' if color == 'w' else 'b'
            elif 'rook' in piece_type:
                key = 'R' if color == 'w' else 'r'
            elif 'queen' in piece_type:
                key = 'Q' if color == 'w' else 'q'
            elif 'king' in piece_type:
                key = 'K' if color == 'w' else 'k'
            if key:
                images[key] = image
        except pygame.error as e:
            print(f"Error loading image '{filepath}': {e}")
            sys.exit()
    return images

if not os.path.exists('images'):
    print("Images directory 'images/' not found. Please create it and add piece images.")
    sys.exit()

PIECE_IMAGES = load_images()

class GUI:
    def __init__(self, board: Board):
        self.board = board
        self.selected_square = None
        self.valid_moves = []
        self.running = True
        self.king_in_check = False
        self.king_square = None
        self.play_again_rect = None
        self.exit_rect = None
        self.promotion_move = None
        self.promotion_pieces = ['Q', 'R', 'B', 'N']
        self.promotion_rects = []

    def draw_board(self):
        for row in range(ROWS):
            for col in range(COLS):
                color = WHITE_COLOR if (row + col) % 2 == 0 else BLACK_COLOR
                pygame.draw.rect(SCREEN, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self):
        for square in range(64):
            piece = self.board.get_piece_at_square(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                piece_key = piece if piece.isupper() else piece.lower()
                piece_image = PIECE_IMAGES.get(piece_key)
                if piece_image:
                    img_rect = piece_image.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2))
                    SCREEN.blit(piece_image, img_rect)

    def highlight_squares(self):
        if self.selected_square is not None:
            self.highlight_square(self.selected_square, TRANSPARENT_BLUE)
            for move_square in self.valid_moves:
                self.highlight_square(move_square, TRANSPARENT_GREEN)
        if self.king_in_check and self.king_square is not None:
            self.highlight_square(self.king_square, TRANSPARENT_RED)

    def highlight_square(self, square, color):
        row = 7 - (square // 8)
        col = square % 8
        rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(color)
        SCREEN.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

    def get_square_clicked(self, pos):
        x, y = pos
        col = x // SQUARE_SIZE
        row = 7 - (y // SQUARE_SIZE)
        if 0 <= col < 8 and 0 <= row < 8:
            return row * 8 + col
        return None

    def main_loop(self, engine, current_node):
        while self.running:
            if not self.board.is_game_over():
                self.draw_board()
                self.highlight_squares()
                self.draw_pieces()

                self.king_in_check = self.board.is_in_check()
                if self.king_in_check:
                    self.king_square = self.board.find_king_square(self.board.white_to_move)
                else:
                    self.king_square = None

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        pygame.quit()
                        sys.exit()

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        if self.promotion_move:
                            # Handle promotion choice
                            for i, rect in enumerate(self.promotion_rects):
                                if rect.collidepoint(pos):
                                    promoted_piece = self.promotion_pieces[i]
                                    self.promotion_move.promoted_piece = promoted_piece
                                    self.board.make_move(self.promotion_move)
                                    current_node = self.update_move_tree(self.promotion_move, current_node, engine)
                                    self.promotion_move = None
                                    break
                        elif self.board.white_to_move:
                            square = self.get_square_clicked(pos)

                            if square is not None:
                                if self.selected_square is None:
                                    piece = self.board.get_piece_at_square(square)
                                    if piece and piece.isupper():
                                        self.selected_square = square
                                        self.valid_moves = [move.to_square for move in self.board.generate_legal_moves() if move.from_square == square]
                                else:
                                    if square == self.selected_square:
                                        # Deselect the piece if clicked again
                                        self.selected_square = None
                                        self.valid_moves = []
                                    elif square in self.valid_moves:
                                        # Proceed to make the move
                                        legal_moves = self.board.generate_legal_moves()
                                        move_found = False
                                        for legal_move in legal_moves:
                                            if legal_move.from_square == self.selected_square and legal_move.to_square == square:
                                                if legal_move.promoted_piece:
                                                    # Prompt for promotion piece
                                                    self.promotion_move = legal_move
                                                else:
                                                    self.board.make_move(legal_move)
                                                    current_node = self.update_move_tree(legal_move, current_node, engine)
                                                move_found = True
                                                break
                                        if move_found:
                                            self.selected_square = None
                                            self.valid_moves = []
                                        else:
                                            self.selected_square = None
                                            self.valid_moves = []
                                    else:
                                        # Check if clicked on another of the player's own pieces to change selection
                                        piece = self.board.get_piece_at_square(square)
                                        if piece and piece.isupper():
                                            self.selected_square = square
                                            self.valid_moves = [move.to_square for move in self.board.generate_legal_moves() if move.from_square == square]
                                        else:
                                            # Clicked on an invalid square; keep the current selection
                                            pass

                if self.promotion_move:
                    self.draw_board()
                    self.draw_pieces()
                    self.draw_promotion_choices()
                    pygame.display.flip()
                    continue

                if not self.board.white_to_move and self.running:
                    pygame.time.delay(500)
                    ai_move = engine.get_ai_move(self.board, current_node, use_move_tree=True, max_depth=3)
                    if ai_move:
                        print(f"AI plays: {ai_move}")
                        move_obj = self.parse_move(ai_move)
                        if move_obj:
                            self.board.make_move(move_obj)
                            current_node = self.update_move_tree(move_obj, current_node, engine)
                        else:
                            print("AI selected an invalid move.")
                            # Do not set self.running = False; let the game detect the end
                    else:
                        print("AI has no legal moves.")
                        # Do not set self.running = False; let the game detect the end

                pygame.display.flip()
            else:
                # Game is over
                self.draw_board()
                self.draw_pieces()
                self.display_game_over()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        if self.play_again_rect.collidepoint(pos):
                            # Restart the game
                            self.restart_game()
                            current_node = engine.move_tree
                        elif self.exit_rect.collidepoint(pos):
                            # Exit the game
                            self.running = False
                            pygame.quit()
                            sys.exit()

                pygame.display.flip()

    def display_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        SCREEN.blit(overlay, (0, 0))

        if self.board.is_checkmate():
            if self.board.white_to_move:
                message = "You lost!"
            else:
                message = "You won!"
        else:
            message = "Draw."

        text = FONT.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        SCREEN.blit(text, text_rect)

        # Add "Play Again" button
        play_again_text = FONT.render("Play Again", True, (255, 255, 255))
        play_again_rect = play_again_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        pygame.draw.rect(SCREEN, (0, 128, 0), play_again_rect.inflate(20, 10))
        SCREEN.blit(play_again_text, play_again_rect)

        # Add "Exit" button
        exit_text = FONT.render("Exit", True, (255, 255, 255))
        exit_rect = exit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        pygame.draw.rect(SCREEN, (128, 0, 0), exit_rect.inflate(20, 10))
        SCREEN.blit(exit_text, exit_rect)

        # Store the rects to detect clicks
        self.play_again_rect = play_again_rect
        self.exit_rect = exit_rect

        pygame.display.flip()

    def restart_game(self):
        self.board = Board()
        self.selected_square = None
        self.valid_moves = []
        self.king_in_check = False
        self.king_square = None
        self.promotion_move = None
        self.promotion_rects = []

    def draw_promotion_choices(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        SCREEN.blit(overlay, (0, 0))

        text = FONT.render("Choose promotion piece:", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        SCREEN.blit(text, text_rect)

        self.promotion_rects = []
        piece_size = SQUARE_SIZE
        y = HEIGHT // 2 - piece_size // 2
        x_start = WIDTH // 2 - 2 * piece_size + 30

        for i, piece_char in enumerate(self.promotion_pieces):
            piece = piece_char if self.board.white_to_move else piece_char.lower()
            image = PIECE_IMAGES[piece]
            x = x_start + i * (piece_size + 20)
            rect = pygame.Rect(x, y, piece_size, piece_size)
            SCREEN.blit(image, rect)
            self.promotion_rects.append(rect)

    def parse_move(self, move_str):
        if move_str in ['O-O', 'O-O-O']:
            if move_str == 'O-O':
                if self.board.white_to_move:
                    from_square = 4
                    to_square = 6
                else:
                    from_square = 60
                    to_square = 62
            else:
                if self.board.white_to_move:
                    from_square = 4
                    to_square = 2
                else:
                    from_square = 60
                    to_square = 58
            is_castling = True
            promoted_piece = None
        else:
            from_square = algebraic_to_square(move_str[0:2])
            to_square = algebraic_to_square(move_str[2:4])
            promoted_piece_char = move_str[4] if len(move_str) == 5 else None
            is_castling = False

        if from_square is None or to_square is None:
            return None

        piece = self.board.get_piece_at_square(from_square)
        if piece is None:
            return None

        captured_piece = self.board.get_piece_at_square(to_square) if self.board.is_square_occupied_by_opponent(to_square) else None

        is_en_passant = False
        if piece.upper() == 'P' and to_square == self.board.en_passant_target:
            is_en_passant = True

        promoted_piece = None
        if promoted_piece_char:
            if piece.isupper():
                #white pawn promoting
                promoted_piece = promoted_piece_char.upper()
            else:
                #black pawn promoting
                promoted_piece = promoted_piece_char.lower()

        move = Move(
            piece=piece,
            from_square=from_square,
            to_square=to_square,
            captured_piece=captured_piece,
            promoted_piece=promoted_piece,
            is_en_passant=is_en_passant,
            is_castling=is_castling
        )

        return move


    def update_move_tree(self, move, current_node, engine):
        if move.is_castling:
            if move.to_square in [6, 62]:
                move_uci = 'O-O'
            else:
                move_uci = 'O-O-O'
        else:
            move_uci = square_to_algebraic(move.from_square) + square_to_algebraic(move.to_square)
            if move.promoted_piece:
                move_uci += f"{move.promoted_piece.upper()}"

        if move_uci in current_node:
            return current_node[move_uci]
        else:
            return {}

class ChessEngine:
    def __init__(self, move_tree):
        self.move_tree = move_tree

    def get_ai_move(self, board, current_node, use_move_tree=True, max_depth=3):
        if use_move_tree and current_node:
            possible_moves = list(current_node.keys())
            if possible_moves:
                selected_move = random.choice(possible_moves)
                return selected_move

        print("Falling back to Minimax algorithm for move selection.")
        best_move = find_best_move(board, max_depth)
        if best_move:
            if best_move.is_castling:
                if best_move.to_square in [6, 62]:
                    return 'O-O'
                else:
                    return 'O-O-O'
            move_str = square_to_algebraic(best_move.from_square) + square_to_algebraic(best_move.to_square)
            if best_move.promoted_piece:
                move_str += f"{best_move.promoted_piece}"
            return move_str.lower()
        else:
            # No legal moves, return None
            return None

def main():
    move_tree_path = r"C:\Users\firefly\Desktop\Chess\pgns\chess_opening_tree2.json"

    try:
        with open(move_tree_path, 'r') as f:
            move_tree = json.load(f)
    except FileNotFoundError:
        print(f"Move tree file not found at {move_tree_path}. Please ensure the file exists.")
        sys.exit()

    engine = ChessEngine(move_tree)
    board = Board()
    gui = GUI(board)
    gui.main_loop(engine, move_tree)

if __name__ == "__main__":
    main()
