import logging
from collections.abc import Iterator
from copy import deepcopy

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from pieces import Piece
from utils import Color, Location


class Board:
    class MoveException(Exception):
        def __init__(self, board: 'Board', message: str, highlights: list[str] | str | None = None, *args):
            # super().__init__(message, *args)
            self.board = board
            self.highlights = highlights
            self.message = message

        def rich_exception(self):
            self.board.logger.error(self.message)
            self.board.console.print(self.message, style="bold red")
            # for num, move in enumerate(self.board.moves):
            #
            #     self.board.console.print(f"{num + 1}. {move}", style="bold green")
            self.board.print(highlights=self.highlights)

    class TempMove:
        def __init__(self, game):
            self.game = game
            self.board = self.game.board
            self.temp_board = None
            self.original_pieces = None
            self.original_captured = None
            self.original_active_player = None
            self.original_moves = None
            self.original_turn_number = None
            self.original_halfmove_counter = None
            self.enpassants = None

        def __enter__(self):
            self.temp_board = deepcopy(self.board)
            self.original_pieces = deepcopy(self.game.pieces)
            self.original_moves = deepcopy(self.game.moves)
            self.original_captured = deepcopy(self.game.captured_pieces)
            self.original_active_player = deepcopy(self.game.active_player)
            self.original_turn_number = deepcopy(self.game.turn_number)
            self.enpassants = deepcopy(self.game.enpassants)
            self.original_halfmove_counter = deepcopy(self.game.halfmove_counter)
            return self.board

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.board.squares.clear()
            self.board.squares.update(self.temp_board.squares)
            self.game.pieces.clear()
            self.game.pieces.update(self.original_pieces)
            self.game.captured_pieces.clear()
            self.game.captured_pieces.update(self.original_captured)
            self.game.active_player = self.original_active_player
            self.game.moves = self.original_moves
            self.game.turn_number = self.original_turn_number
            self.game.halfmove_counter = self.original_halfmove_counter
            self.game.enpassants = self.enpassants

    _precomputed_square_names = [f'{letter}{number}' for letter in 'abcdefgh' for number in range(1, 9)]

    def __init__(self, loglevel="ERROR", console=None):
        """
        Initialize the chess board. Set up required variables and clear the board.
        """
        self.console = Console() if console is None else console
        self.squares: dict[str, None | Piece] = {name: None for name in Board._precomputed_square_names}
        self.black_square_color = 'white'
        self.white_square_color = 'bright_white'
        self.black_piece_color = 'blue'
        self.white_piece_color = 'green'
        self.highlight_color = 'red'
        logging.basicConfig(level=loglevel, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True, console=self.console, markup=True, show_path=False)])
        self.logger = logging.getLogger("rich")
        self.logger.setLevel(loglevel)

    def __deepcopy__(self, memo):
        cls = self.__class__
        backup_board = cls.__new__(cls)
        backup_board.__init__()
        memo[id(self)] = backup_board

        for k, v in self.__dict__.items():
            if k in ['console', 'logger']:
                continue
            elif k == 'pieces':
                getattr(backup_board, k).update(v)
                copied_dict = {}
                for name, contents in v.items():
                    copied_dict[name] = deepcopy(contents, memo)
                setattr(backup_board, k, copied_dict)
            else:
                setattr(backup_board, k, deepcopy(v, memo))
        return backup_board

    def __eq__(self, other):
        if self.squares != other.squares:
            return False
        return True

    def __getitem__(self, location) -> Piece | None:
        """
        Overload the [] operator to access squares on the board.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        Piece object if the square is occupied else None.
        """
        if isinstance(location, str):
            return self.squares[location]
        elif isinstance(location, Location):
            return self.squares[location.location]

    def __setitem__(self, square: str | Location, piece: Piece | None):
        if isinstance(square, Location):
            square = square.location
        self.squares[square] = piece
        if piece is not None:
            piece.location = square

    def add_piece(self, piece: Piece):
        location = str(piece.location)
        if self[location] is not None:
            raise self.MoveException(self, f"Cannot add {piece} to {location}, already occupied by {self.squares[location]}")
        self[location] = piece

    def move(self, start: Location, end: Location | None, force=False):
        if self[start] is None:
            raise Board.MoveException(self, f"No piece at {start}")
        if self[end] is None:
            # No capture
            if not self[start].can_move_to(end, self):
                raise Board.MoveException(self, f"{self[start].__class__.__name__.capitalize()} at {start} can't move to {end}")
            captured_piece = None
        else:
            if not self[start].can_take(end, self):
                raise Board.MoveException(self, f"{self[start].__class__.__name__.capitalize()} at {start} cannot take {self[end].__class__.__name__.capitalize()} at {self[end]}")
            captured_piece = self[end]
            captured_piece.location = None
        self[end], self[start] = self[start], None
        return captured_piece

    def iter_square_names(self) -> Iterator[str]:
        """
        Iterate over all squares of the board from left to right and top to bottom.

        Yields:
        str: The square in chess notation, for example, 'a1', 'a2'...'h8'.
        """
        return iter(self._precomputed_square_names)

    def clear(self):
        """
        Clear the board.
        """
        self.squares: dict[str, None | Piece] = {name: None for name in Board._precomputed_square_names}

    @staticmethod
    def get_square_color(square: Location) -> Color:
        """
        Check the color of the square, using the board's 8x8 grid and the chess rule of alternation.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        str: "black" if the square is black, "white" if the square is white.
        """
        return Color.BLACK if (square.int_file - 98 + square.rank) % 2 == 0 else Color.WHITE

    @staticmethod
    def get_intermediate_squares(start: Location | str, end: Location | str) -> Iterator[Location]:
        """
        Get all squares that a piece must cross to get from start to end.
        This does not include the end square but includes the start square.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        end (str): The ending square in chess notation, for example, 'e7'.

        Yields:
        str: The squares in the path from start to end.
        """
        if isinstance(start, str):
            start = Location(start)
        if isinstance(end, str):
            end = Location(end)

        move_distance = start - end

        if abs(move_distance[0]) == abs(move_distance[1]):
            # Diagonal move
            step_x = 1 if start.int_file < end.int_file else -1
            step_y = 1 if start.rank < end.rank else -1
            for i in range(1, abs(move_distance[0])):
                tmp = f'{chr(start.int_file + i * step_x)}{start.rank + i * step_y}'
                yield Location(tmp)

        elif abs(move_distance[0]) == 0:
            # Vertical move e.g. B6 -> B2 - change in Rank
            step = 1 if start.rank < end.rank else -1
            for rank in range(start.rank + step, end.rank, step):
                yield Location(f'{start.file}{rank}')

        elif abs(move_distance[1]) == 0:
            # Horizontal move e.g. D2 -> H2 - change in File
            step = 1 if start.int_file < end.int_file else -1
            for file in range(start.int_file + step, end.int_file, step):
                yield Location(f'{chr(file)}{end.rank}')

    def is_move_clear(self, start: Location, end: Location) -> bool:
        """
        Check if a move from start square to end square is clear, i.e., there are no other pieces blocking the way.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        end (str): The ending square in chess notation, for example, 'e7'.

        Returns:
        bool: True if path is clear, False otherwise.
        """
        intermediate_squares = list(self.get_intermediate_squares(start, end))
        if not intermediate_squares:
            return True
        for square in intermediate_squares:
            if self[square] is not None:
                return False
        return True

    @staticmethod
    def is_valid_square_name(location: str) -> bool:
        """
        Check if the denoted location is within the boundaries of the chess board.

        Parameters:
        location (str): The location to be checked, e.g. 'a1'.

        Returns:
        bool: True if the location is within the board, False otherwise.
        """
        return location[0] in "abcdefgh" and location[1] in "12345678"

    def print(self, highlights: str | list[str] | None = None) -> None:
        self.console.print(self.create_board_text(highlights))

    def create_board_text(self, highlights: str | list[str] = None) -> Text:
        if isinstance(highlights, str):
            highlights = [highlights]

        # Add file labels at the top
        board_text = Text("a b c d e f g h\n", style="bold white")

        for number in range(8, 0, -1):
            # Add rank label at the start of each line
            board_text.append(f"{number} ", style="bold white")

            for letter in "abcdefgh":
                square = f'{letter}{number}'
                square_color = self.get_square_color(Location(square))
                piece = self.squares[square]

                if piece is not None:
                    square_text = f'{piece} '
                    piece_color = self.black_piece_color if piece.color == Color.BLACK else self.white_piece_color
                else:
                    square_text = '  '
                    piece_color = None

                if highlights is not None and square in highlights:
                    square_color = self.highlight_color
                else:
                    square_color = self.black_square_color if square_color == "black" else self.white_square_color

                piece_color = square_color if piece_color is None else piece_color
                square_style = f"{piece_color} on {square_color}"
                board_text.append(text=square_text, style=square_style)

            # Add rank label at the end of each line
            board_text.append(f" {number}\n", style="bold")

        # Add file labels at the bottom
        board_text.append("a b c d e f g h", style="bold")

        return board_text
