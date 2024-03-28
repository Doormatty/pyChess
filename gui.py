from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

from board import Board
from pieces import Pawn, Knight, Bishop, Rook, Queen, King, Piece


class ChessSquare(Button):

    def __init__(self, name: str, board_widget: 'ChessBoard', color, **kwargs):
        self.name = name
        self.board_widget = board_widget
        super().__init__(background_color=color, background_normal='', background_down='', halign='center', valign='center', font_name='DejaVuSans-Bold.ttf', **kwargs)
        self.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.bind(size=self.adjust_font_size)
        self.piece = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"ChessSquare(name={self.name}, board_widget={self.board_widget})"

    @staticmethod
    def adjust_font_size(button: Button, new_size: tuple):
        max_font_size = min(new_size[0], new_size[1])
        button.font_size = max_font_size * 1.2

    def add(self, piece: Piece):
        self.piece = piece
        self.text = str(self.piece)
        self.color = self.piece.color

    def clear(self):
        self.piece = None
        self.text = ''

    @staticmethod
    def square_to_index(square: str) -> int:
        try:
            col = ord('h') - ord(square[0])
        except TypeError:
            return -1  # Return an invalid index
        row = int(square[1]) - 1  # Rows are numbered from 1 to 8, starting from the top
        return row * 8 + col

    def draw_moves(self):
        if self.piece is None:
            return None
        possible_moves = self.piece.get_all_possible_moves()
        for move in possible_moves:
            if self.name == move:
                continue
            elif self.board_widget[move].piece is not None and self.piece.can_take(move):
                self.board_widget[move].background_color = self.board_widget.capture_background
            elif self.piece.can_move_to(move) and self.board_widget[move].piece is None:
                self.board_widget[move].background_color = self.board_widget.highlight_color
        self.background_color = self.board_widget.selected_background

    def on_press(self) -> None:
        Logger.info(f"ChessSquare: Square {self.name} pressed")
        if self.piece is not None:
            Logger.info(f"ChessSquare: Piece {self.piece.location} selected")
        self.board_widget.reset_square_colors()

        if self.piece is not None:
            # If there is a piece in this square
            self.parent.app.selected_piece = self.piece
            Logger.info(f"ChessSquare: self.piece.location: {self.piece.location}")
            self.draw_moves()
        elif self.parent.app.selected_piece is not None:
            if self.parent.app.selected_piece == self.piece:
                self.parent.app.selected_piece = None
            else:
                Logger.info(f"ChessSquare: Selected Piece {self.parent.app.selected_piece.location}")
                Logger.info(f"ChessSquare: Trying to move to {self.name}")
                self.parent.app.board.move(self.parent.app.selected_piece.location, self.name)
                self.parent.app.selected_piece = None
                self.parent.app.load_state_from(self.parent.app.board)


class ChessBoard(GridLayout):
    def __init__(self, app, **kwargs):
        super().__init__(cols=8, rows=8, size_hint_x=1 / 3, padding=[0, 100, 0, 100], **kwargs)
        self.app = app
        self.squares = None
        self.rect_squares = None
        self.white_piece_color = kwargs.get("white_piece_color", [1, 1, 1, 1])
        self.black_piece_color = kwargs.get("black_piece_color", [0, 0, 0, 1])
        self.background_color = kwargs.get("background_color", [0.3, 0.3, 0.3, 1])
        self.white_square_color = kwargs.get("white_square_color", [0.6, 0.6, 0.6, 1])
        self.black_square_color = kwargs.get("black_square_color", [0.02, 0.20, 0.20, 1])
        self.highlight_color = kwargs.get("highlight_color", [1, 0, 0, 1])
        self.selected_background = kwargs.get("selected_background", [0, 0.67, 0.56])
        self.capture_background = kwargs.get("capture_background", [0, 0.49, 0.67])

        # Grid is filled left to right then top to bottom
        for number in range(8, 0, -1):
            for letter in "abcdefgh":
                self.add_widget(ChessSquare(name=f"{letter}{number}", board_widget=self, color=self.get_square_color(f"{letter}{number}")))

    def __getitem__(self, item: str) -> ChessSquare:
        index = ChessSquare.square_to_index(item)
        return self.children[index]

    def add(self, index: str | int, piece: King | Queen | Knight | Bishop | Rook | Pawn):
        self[index].add(piece)

    def get_square_color(self, square):
        is_dark_square = ((8 - int(square[1])) + (ord(square[0]) - ord('a'))) % 2 == 0
        return self.black_square_color if is_dark_square else self.white_square_color

    def reset_square_colors(self):
        for letter in "abcdefgh":
            for number in range(1, 9):
                self[f"{letter}{number}"].background_color = self.get_square_color(f"{letter}{number}")


class ChessGui(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = Board()
        self.left_layout = BoxLayout(orientation='vertical', size_hint_x=1 / 3)
        self.right_layout = BoxLayout(orientation='vertical', size_hint_x=1 / 3)
        self.board_widget = ChessBoard(self)
        self.rect_left = None
        self.rect_right = None
        self.rect_squares = None
        self.current_player = "white"
        self.turn_counter = 0
        self.halfturn_counter = 0
        self.selected_square = None
        self.selected_piece = None

    def build(self):
        master_layout = BoxLayout(orientation='horizontal')
        with self.left_layout.canvas.before:
            Color(*self.board_widget.background_color)
            self.rect_left = Rectangle(size=self.left_layout.size, pos=self.left_layout.pos)

        with self.right_layout.canvas.before:
            Color(*self.board_widget.background_color)
            self.rect_right = Rectangle(size=self.right_layout.size, pos=self.right_layout.pos)

        with self.board_widget.canvas.before:
            Color(*self.board_widget.background_color)
            self.rect_squares = Rectangle(size=self.board_widget.size, pos=self.board_widget.pos)

        # Add binding to update rectangle size and position when layouts change
        self.left_layout.bind(pos=self.update_rect, size=self.update_rect)
        self.right_layout.bind(pos=self.update_rect, size=self.update_rect)
        self.board_widget.bind(pos=self.update_rect, size=self.update_rect)

        # Add widgets to master_layout
        master_layout.add_widget(self.left_layout)
        master_layout.add_widget(self.board_widget)
        master_layout.add_widget(self.right_layout)

        self.board_widget.bind(size=self.adjust_square_sizes)
        return master_layout

    def adjust_square_sizes(self, instance, *args):

        # Calculate the size for each square
        square_size = min(instance.width / 8, instance.height / 8)

        # Update the size of each square
        for square in self.board_widget.children:
            square.size_hint = (None, None)
            square.size = (square_size, square_size)
            square.text_size = (square_size, square_size)

    def update_rect(self, instance, *args):
        if instance == self.left_layout:
            self.rect_left.pos = instance.pos
            self.rect_left.size = instance.size
        elif instance == self.right_layout:
            self.rect_right.pos = instance.pos
            self.rect_right.size = instance.size
        elif instance == self.board_widget:
            self.rect_squares.pos = instance.pos
            self.rect_squares.size = instance.size

    def load_state_from(self, board: Board):
        for square_name in Board.iter_square_names():
            piece = board[square_name]
            if piece is not None:
                Logger.debug(f"ChessGui: adding {piece} {piece.location} to {square_name}")
                self.board_widget[square_name].add(piece)
                assert piece == self.board_widget[square_name].piece
            else:
                self.board_widget[square_name].clear()

    def save_state_to(self, board: Board):
        for square_name in Board.iter_square_names():
            piece = self.board_widget[square_name].piece
            if piece is not None:
                board[square_name] = piece
            else:
                board[square_name] = None


if __name__ == "__main__":
    app = ChessGui()
    board = Board()
    board.initialize_board()
    app.load_state_from(board)
    app.run()
