from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

from pieces import Pawn, Knight, Bishop, Rook, Queen, King, Piece


class ChessSquare(Button):

    def __init__(self, index, board, color, **kwargs):
        super().__init__(background_color=color, background_normal='', background_down='', halign='center', valign='center', font_name='DejaVuSans-Bold.ttf', **kwargs)
        self.index = index
        self.board = board
        self.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.bind(size=self.adjust_font_size)
        self.piece = None

    @staticmethod
    def adjust_font_size(button, new_size):
        max_font_size = min(new_size[0], new_size[1])
        button.font_size = max_font_size * 1.2

    def add(self, piece: Piece):
        self.piece = piece
        self.text = str(self.piece)
        self.color = self.piece.color

    def clear(self):
        self.piece = None
        self.text = ''

    def reset_background_color(self):
        self.background_color = self.board.white_square_color if (self.index // 8 + self.index) % 2 == 0 else self.board.black_square_color

    @staticmethod
    def index_to_square(number):
        if not 0 <= number <= 63:
            return "Invalid number"
        file = chr(ord('a') + (number % 8))  # Horizontal (columns 'a' to 'h')
        rank = 1 + (number // 8)  # Vertical (rows 1 to 8 from bottom to top)
        return f"{file}{rank}"

    @staticmethod
    def square_to_index(square):
        if len(square) != 2 or square[0] < 'a' or square[0] > 'h' or square[1] < '1' or square[1] > '8':
            raise ValueError("Invalid square")
        file = ord(square[0]) - ord('a')  # Horizontal
        rank = int(square[1]) - 1  # Vertical
        return rank * 8 + file

    def on_press(self):
        print(f"Square {self.index} {self.index_to_square(self.index)} pressed")
        self.board.reset_square_colors()

        if self.piece is not None:
            possible_moves = self.piece.get_all_possible_moves()
            for move in possible_moves:
                self.board[self.square_to_index(move)].background_color = [1, 0, 0, 1]


class ChessBoard(GridLayout):
    def __init__(self, app, background_color=None, white_square_color=None, black_square_color=None, white_piece_color=None, black_piece_color=None, **kwargs):
        self.white_piece_color = [1, 1, 1, 1] if white_piece_color is None else white_piece_color
        self.black_piece_color = [0, 0, 0, 1] if black_piece_color is None else black_piece_color
        super().__init__(cols=8, rows=8, size_hint_x=1 / 3, padding=[0, 100, 0, 100], **kwargs)
        self.app = app
        self.squares = None
        self.rect_squares = None
        self.background_color = [0.3, 0.3, 0.3, 1] if background_color is None else background_color
        self.white_square_color = [0.6, 0.6, 0.6, 1] if white_square_color is None else white_square_color
        self.black_square_color = [0.02, 0.20, 0.20, 1] if black_square_color is None else black_square_color
        for i in range(64):
            self.add_widget(ChessSquare(index=i, board=self, color=self.white_square_color if (i // 8 + i) % 2 == 0 else self.black_square_color))

    def __getitem__(self, item):
        if isinstance(item, str):
            try:
                item = int(item)
            except ValueError:
                item = ChessSquare.square_to_index(item)
        return self.children[item]

    def add(self, index, piece):
        self[index].add(piece)

    def reset_square_colors(self):
        for i in range(64):
            self[i].background_color = self.white_square_color if (i // 8 + i) % 2 == 0 else self.black_square_color


class ChessGui(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.left_layout = None
        self.right_layout = None
        self.board = None
        self.rect_left = None
        self.rect_right = None
        self.rect_squares = None
        self.background_color = [0.3, 0.3, 0.3, 1]
        self.current_player = "white"
        self.turn_counter = 0
        self.halfturn_counter = 0
        self.selected_square = None

    def build(self):
        master_layout = BoxLayout(orientation='horizontal')

        self.left_layout = BoxLayout(orientation='vertical', size_hint_x=1 / 3)
        with self.left_layout.canvas.before:
            Color(*self.background_color)
            self.rect_left = Rectangle(size=self.left_layout.size, pos=self.left_layout.pos)

        self.right_layout = BoxLayout(orientation='vertical', size_hint_x=1 / 3)
        with self.right_layout.canvas.before:
            Color(*self.background_color)
            self.rect_right = Rectangle(size=self.right_layout.size, pos=self.right_layout.pos)

        self.board = ChessBoard(self, background_color=self.background_color)
        with self.board.canvas.before:
            Color(*self.background_color)
            self.rect_squares = Rectangle(size=self.board.size, pos=self.board.pos)

        # Add binding to update rectangle size and position when layouts change
        self.left_layout.bind(pos=self.update_rect, size=self.update_rect)
        self.right_layout.bind(pos=self.update_rect, size=self.update_rect)
        self.board.bind(pos=self.update_rect, size=self.update_rect)

        # Add widgets to master_layout
        master_layout.add_widget(self.left_layout)
        master_layout.add_widget(self.board)
        master_layout.add_widget(self.right_layout)

        self.board.bind(size=self.adjust_square_sizes)
        self.load_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1")
        return master_layout

    def adjust_square_sizes(self, instance, *args):

        # Calculate the size for each square
        square_size = min(instance.width / 8, instance.height / 8)

        # Update the size of each square
        for square in self.board.children:
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
        elif instance == self.board:
            self.rect_squares.pos = instance.pos
            self.rect_squares.size = instance.size

    def load_fen(self, layout):
        def get_color(piece):
            if piece.isupper():
                return 'white'
            else:
                return 'black'

        piece_dict = {"r": Rook, "k": King, "b": Bishop, "n": Knight, "p": Pawn, "q": Queen}
        board_layout = layout.split(' ')[0]
        current_player = layout.split(' ')[1]
        castles = layout.split(' ')[2]
        enpassant = layout.split(' ')[3]
        self.halfturn_counter = int(layout.split(' ')[4])
        self.turn_counter = int(layout.split(' ')[5])
        self.current_player = "white" if current_player.lower() == "w" else "black"
        expanded_layout = ""
        for char in board_layout:
            if char.isdigit():
                expanded_layout += ' ' * int(char)
            elif char == "/":
                continue
            else:
                expanded_layout += char
        for index, piece in enumerate(expanded_layout):
            if piece != ' ':
                color = get_color(piece)
                piece_class = piece_dict[piece.lower()]
                self.board.add(63-index, piece_class(color=color, location=index, board=self.board))


if __name__ == "__main__":
    ChessGui().run()
