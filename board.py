import io
import logging
import re
from collections import defaultdict
from collections.abc import Iterator
from copy import deepcopy

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from pieces import Pawn, Knight, Bishop, Rook, Queen, King, Piece


def rich_pprint(obj):
    with io.StringIO() as buf, Console(file=buf, force_terminal=True) as console:
        console.print(obj)
        return buf.getvalue()


# TODO - Write function that returns a dictionary of pieces, with the values being all possible moves and captures possible by that piece.
# TODO - Write function that takes the above mentioned dictionary, and provides scores for each possible move/capture
# TODO - Handle Check and Checkmate

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
        def __init__(self, board):
            self.board = board
            self.temp_board = None

        def __enter__(self):
            self.temp_board = deepcopy(self.board)
            return self.board

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.board.pieces.clear()
            self.board.pieces.update(self.temp_board.pieces)
            self.board.squares.clear()
            self.board.squares.update(self.temp_board.squares)
            self.board.captured_pieces.clear()
            self.board.captured_pieces.update(self.temp_board.captured_pieces)
            self.board.moves.clear()
            self.board.moves.extend(self.temp_board.moves)

    _precomputed_square_names = [f'{letter}{number}' for letter in 'abcdefgh' for number in range(1, 9)]

    def __init__(self, loglevel="ERROR"):
        """
        Initialize the chess board. Set up required variables and clear the board.
        """
        self.console = Console()
        self.pieces = {"white": [], "black": []}
        self.squares: dict[str, None | Piece] = {name: None for name in Board._precomputed_square_names}
        self.captured_pieces = {"white": [], "black": []}
        self.active_player = 'white'
        self.turn_number = 0
        self.moves = []
        self.halfmove_counter = 0
        self.enpassants = []
        self.castling = []
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
            elif k in ['squares', 'pieces', 'captured_pieces']:
                getattr(backup_board, k).update(v)
                copied_dict = {}
                for name, contents in v.items():
                    copied_dict[name] = deepcopy(contents, memo)
                setattr(backup_board, k, copied_dict)
            else:
                setattr(backup_board, k, deepcopy(v, memo))
        return backup_board

    def __eq__(self, other):
        if self.turn_number != other.turn_number:
            return False
        if self.moves != other.moves:
            return False
        if self.captured_pieces != other.captured_pieces:
            return False
        if self.enpassants != other.enpassants:
            return False
        if self.castling != other.castling:
            return False
        if self.squares != other.squares:
            return False
        if self.pieces != other.pieces:
            return False
        if self.active_player != other.active_player:
            return False
        if self.halfmove_counter != other.halfmove_counter:
            return False
        return True

    def __getitem__(self, square) -> Piece | None:
        """
        Overload the [] operator to access squares on the board.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        Piece object if the square is occupied else None.
        """
        return self.squares[square]

    def __setitem__(self, square: str, piece: Piece | None):
        self.squares[square] = piece
        if piece is not None:
            piece.location = square

    @property
    def antiplayer(self):
        return 'black' if self.active_player == 'white' else 'white'

    def add_piece(self, piece: Piece):
        color = piece.color
        location = piece.location
        if self[location] is not None:
            raise self.MoveException(self, f"Cannot add {piece} to {location}, already occupied by {self.squares[location]}")
        self.pieces[color].append(piece)
        self[location] = piece

    def _force_move(self, start: str, end: str):
        piece = self[start]
        self[start] = None
        self[end] = piece

    def determine_move_type(self, start, end=None):
        if start in ("O-O", "O-O-O"):
            return start
        if abs(int(start[1])-int(end[1]))==1 and self[end] is None and end in self.enpassants and self[start].__class__.__name__ == "Pawn":
            return "enpassant"
        return None

    def move(self, start=None, end=None, special=None, override=False):
        self.validate_move(start, end)
        if special is None:
            special = self.determine_move_type(start,end)
        if special is None:
            self.handle_standard_move(start, end)
        elif special in ("O-O", "O-O-O"):
            self.handle_castling(special)
        elif special == "enpassant":
            self.handle_enpassant(start, end)
        self.finalize_move(start, end, special, override)

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
        self.squares = defaultdict(lambda: None)
        self.pieces = {"white": [], "black": []}
        self.captured_pieces = {"white": [], "black": []}
        self.turn_number = 0
        self.moves = []
        self.halfmove_counter = 0
        self.enpassants = []
        self.castling = []
        self.active_player = "white"

    @staticmethod
    def get_square_color(square: str) -> str:
        """
        Check the color of the square, using the board's 8x8 grid and the chess rule of alternation.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        str: "black" if the square is black, "white" if the square is white.
        """
        return "black" if (ord(square[0].lower()) - ord('a') + 1 + int(square[1])) % 2 == 0 else "white"

    @staticmethod
    def get_move_distance(start: str, end: str) -> tuple[int, int]:
        """
        Computes the vertical and horizontal distance between two squares.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        end (str): The ending square in chess notation, for example, 'e7'.

        Returns:
        A tuple of (horizontal_distance, vertical_distance).
        """
        vertical = int(end[1]) - int(start[1])
        horizontal = abs(ord(end[0].lower()) - ord(start[0].lower()))
        return horizontal, vertical

    @staticmethod
    def get_intermediate_squares(start: str, end: str) -> Iterator[tuple[str, str]]:
        """
        Get all squares that a piece must cross to get from start to end.
        This does not include the end square but includes the start square.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        end (str): The ending square in chess notation, for example, 'e7'.

        Yields:
        str: The squares in the path from start to end.
        """
        move_distance = Board.get_move_distance(start, end)

        if abs(move_distance[0]) == 0:
            # Vertical move
            step = 1 if start[1] < end[1] else -1
            for vertical in range(int(start[1]) + step, int(end[1]), step):
                yield f'{start[0]}{vertical}'

        elif abs(move_distance[1]) == 0:
            # Horizontal move
            step = 1 if ord(start[0]) < ord(end[0]) else -1
            for horizontal in range(ord(start[0]) + step, ord(end[0]), step):
                yield f'{chr(horizontal)}{end[1]}'

        elif abs(move_distance[0]) == abs(move_distance[1]):
            # Diagonal move
            step_x = 1 if ord(start[0]) < ord(end[0]) else -1
            step_y = 1 if int(start[1]) < int(end[1]) else -1
            for i in range(1, abs(move_distance[0])):
                yield f'{chr(ord(start[0]) + i * step_x)}{int(start[1]) + i * step_y}'

    def is_move_clear(self, start: str, end: str) -> bool:
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

    def castle(self, move: str):
        can_castle = self.can_castle()
        color = self.active_player
        if move == "O-O":
            if not can_castle[color]['kingside']:
                raise self.MoveException(self, f"{color} cannot castle Kingside.")
            if color == "white":
                self._force_move("e1", "g1")
                self._force_move("h1", "f1")
                self["g1"].has_moved = True
                self["f1"].has_moved = True
            else:
                self._force_move("e8", "g8")
                self._force_move("h8", "f8")
                self["g8"].has_moved = True
                self["f8"].has_moved = True
        elif move == "O-O-O":
            if not can_castle[color]['queenside']:
                raise self.MoveException(self, f"{color} cannot castle Queenside.")
            if color == "white":
                self._force_move("e1", "c1")
                self._force_move("a1", "e1")
                self["c1"].has_moved = True
                self["e1"].has_moved = True
            else:
                self._force_move("e8", "c8")
                self._force_move("a8", "e8")
                self["c8"].has_moved = True
                self["e8"].has_moved = True
        self.halfmove_counter += 1
        self.active_player = 'white' if self.active_player == 'black' else 'black'

    def can_castle(self) -> dict:
        retval = {'white': {}, 'black': {}}
        if self['e1'] is not None and not self['e1'].has_moved:
            retval['white']['queenside'] = self['a1'] is not None and not self['a1'].has_moved and not self.who_can_capture('e1', color_filter='black') and not self.who_can_capture('d1', color_filter='black') and not self.who_can_capture('c1', color_filter='black') and not self.who_can_capture('b1', color_filter='black')
            retval['white']['kingside'] = self['h1'] is not None and not self['h1'].has_moved and not self.who_can_capture('e1', color_filter='black') and not self.who_can_capture('f1', color_filter='black') and not self.who_can_capture('g1', color_filter='black')
        if self['e8'] is not None and not self['e8'].has_moved:
            retval['black']['queenside'] = self['a8'] is not None and not self['a8'].has_moved and not self.who_can_capture('e8', color_filter='white') and not self.who_can_capture('d8', color_filter='white') and not self.who_can_capture('c8', color_filter='white') and not self.who_can_capture('b8', color_filter='white')
            retval['black']['kingside'] = self['h8'] is not None and not self['h8'].has_moved and not self.who_can_capture('e8', color_filter='white') and not self.who_can_capture('f8', color_filter='white') and not self.who_can_capture('g8', color_filter='white')
        return retval

    def fen_can_castle(self) -> str:
        """
        Translates the output of `self.can_castle()` to Fen castling style

        Returns:
        str: A string representing the castling availability. 'KQkq' means that both kings can castle to both sides.
        '-' means no king can castle anymore.
        """
        can_castle = self.can_castle()
        retval = f'{"K" if can_castle["white"]["kingside"] else ""}{"Q" if can_castle["white"]["queenside"] else ""}{"k" if can_castle["black"]["kingside"] else ""}{"q" if can_castle["black"]["queenside"] else ""}'
        if retval == "":
            retval = '-'
        return retval

    def describe_move(self, parsed_move) -> str:
        move = parsed_move['move']
        if move in ("O-O", "O-O-O"):
            if move == "O-O-O":
                return f"{self.active_player.capitalize()}: castles Queenside"
            else:
                return f"{self.active_player.capitalize()}: castles Kingside"

        if parsed_move['capture']:
            return f"{self.active_player.capitalize()}: {parsed_move['start_square']} to {parsed_move['end_square']}, {self.squares[parsed_move['start_square']].__class__.__name__} takes {self.squares[parsed_move['end_square']].__class__.__name__}"
        else:
            return f"{self.active_player.capitalize()}: {parsed_move['start_square']} to {parsed_move['end_square']}"

    def compact_move(self, move: str):
        parsed_move = self.parse_move(move)
        capture = parsed_move['capture']
        # self.logger.debug(f"Parsed {move} into {parsed_move}")
        expanded_move = self.expand_move(parsed_move)
        if move in ("O-O", "O-O-O"):
            self.move(special=move)
            self.logger.info(self.describe_move(parsed_move))
        else:
            parsed_move['start_square'] = expanded_move[0]
            parsed_move['end_square'] = expanded_move[1]
            description = self.describe_move(parsed_move)
            try:
                if len(expanded_move) == 3:
                    self.move(start=expanded_move[0], end=expanded_move[1], special=expanded_move[2])
                else:
                    self.move(start=expanded_move[0], end=expanded_move[1])
            except self.MoveException as e:
                self.logger.error(e)
                raise
            else:
                self.logger.info(description)

    @staticmethod
    def parse_move(move: str) -> dict:
        pattern = r'((?P<start_type>[KQNBR])?(?P<start_square>[a-h][1-8]?)?(?P<capture>x)?(?P<end_type>[KQNBR])?(?P<end_square>[a-h][1-8])(?P<check>\+)?)?(?P<kscastle>O-O)?(?P<qscastle>O-O-O)?(?P<checkmate>#)?'
        parts = re.match(pattern, move)
        type_dict = {'K': King, 'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight}
        return {'move': move,
                'start_type': type_dict[parts['start_type']] if parts['start_type'] is not None else Pawn,
                'end_type': type_dict[parts['end_type']] if parts['end_type'] is not None else None,
                'start_square': parts['start_square'],
                'end_square': parts['end_square'],
                'capture': True if parts['capture'] else False,
                'check': True if parts['check'] else False,
                'checkmate': True if parts['checkmate'] else False,
                'king_castle': True if parts['kscastle'] else False,
                'queen_castle': True if parts['qscastle'] else False}

    def does_move_cause_self_check(self, start, end):
        with self.TempMove(self):
            self.move(start, end, override=True)
            is_check = self.is_king_in_check(self.active_player)
            if is_check:
                self.is_king_in_check(self.active_player)
            return is_check

    def is_king_in_check(self, player):
        king = [piece for piece in self.pieces[player] if piece.__class__.__name__ == 'King'][0]
        attackers = self.who_can_capture(king.location)
        if attackers:
            self.logger.info(f"King's attackers found: {attackers}")
            return True
        return False

    def expand_move(self, parsed_move) -> tuple[str, str | None] | tuple[str, str | None, str]:
        if parsed_move['king_castle'] or parsed_move['queen_castle']:
            return parsed_move, None

        start_square, end_square = self.determine_start_and_end_squares(parsed_move)
        possibles = self.find_possible_moves(parsed_move, start_square, end_square)
        possibles_after_self_check = [p for p in possibles if not self.does_move_cause_self_check(p.location, end_square)]

        if len(possibles_after_self_check) > 1:
            raise self.MoveException(self, f"Ambiguous move: {parsed_move['move']} could refer to multiple pieces.")

        return possibles_after_self_check[0].location, end_square

    def determine_start_and_end_squares(self, parsed_move):
        start_square = parsed_move['start_square']
        end_square = parsed_move['end_square']
        if parsed_move['start_type'].__qualname__ == 'King' and start_square is None:
            start_square = self.find_king_location(self.active_player)
        return start_square, end_square

    def find_possible_moves(self, parsed_move, start_square, end_square):
        if parsed_move['capture']:
            return self.find_possible_captures(parsed_move, start_square, end_square)
        else:
            return self.who_can_move_to(end_square, self.active_player, parsed_move['start_type'].__qualname__, start_square[0] if start_square else None)

    def find_possible_captures(self, parsed_move, start_square, end_square):
        if end_square in self.enpassants and parsed_move['start_type'].__qualname__ == 'Pawn' and self.squares[end_square] is None:
            return self.handle_enpassant_possibility(parsed_move, start_square, end_square)
        elif self.squares[end_square] is None:
            raise self.MoveException(self, f"Illegal capture: no piece at {end_square}.")
        return self.who_can_capture(end_square, parsed_move['start_type'].__qualname__, start_square[0] if start_square else None, self.antiplayer)

    def handle_enpassant_possibility(self, parsed_move, start_square, end_square):
        capture_rank = '6' if self.active_player == 'white' else '3'
        square_to_capture = f'{end_square[0]}{capture_rank}'
        possibles = self.who_can_capture(end_square, 'Pawn', start_square[0] if start_square else None, self.active_player)
        if len(possibles) != 1:
            raise self.MoveException(self, "En passant capture ambiguity.")
        return possibles

    def find_king_location(self, player_color):
        return next(piece.location for piece in self.pieces[player_color] if isinstance(piece, King))

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

    def export_to_fen(self):
        """
        Export the current game state to FEN (Forsyth–Edwards Notation) string.

        Returns:
        str: The FEN string representing the current game state.
        """
        fen = ""
        for number in range(8, 0, -1):
            empty_count = 0
            for letter in "abcdefgh":
                piece = self.squares[f'{letter}{number}']
                if piece is None:
                    empty_count += 1
                elif isinstance(piece, Piece):
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    if piece.__class__.__name__ == "Knight":
                        piece_name = "N"
                    else:
                        piece_name = str(piece.__class__.__name__)[0]
                    if piece.color == "white":
                        fen += piece_name.upper()
                    else:
                        fen += piece_name.lower()
            if empty_count > 0:
                fen += str(empty_count)
            if number > 1:
                fen += "/"
        fen += f"{' w' if self.turn_number % 2 == 1 else ' b'} {self.fen_can_castle()}"
        fen += " -"  # En passant target square: This is a square over which a pawn has just passed while moving two squares. If there is no en passant target square, use "-"
        fen += f" {str(self.halfmove_counter)} {str(self.turn_number)}"
        return fen

    def initialize_board(self):
        """
        Initialize the board with a standard set of pieces.
        """
        self.turn_number = 1
        self.active_player = "white"

        for square in self.iter_square_names():
            row = square[1]
            col = square[0]

            if row in ('3', '4', '5', '6'):
                self.squares[square] = None
            elif row == '2':
                self.add_piece(piece=Pawn('white', location=square))
            elif row == '7':
                self.add_piece(piece=Pawn('black', location=square))
            elif row in ('1', '8'):
                color = 'white' if row == '1' else 'black'

                if col in ('a', 'h'):
                    self.add_piece(piece=Rook(color, location=square))
                elif col in ('b', 'g'):
                    self.add_piece(piece=Knight(color, location=square))
                elif col in ('c', 'f'):
                    self.add_piece(piece=Bishop(color, location=square))
                elif col == 'd':
                    self.add_piece(piece=Queen(color, location=square))
                elif col == 'e':
                    self.add_piece(piece=King(color, location=square))

    def who_can_move_to(self, location, color=None, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")

        color = color or self.active_player
        pieces = []
        for piece in self.pieces[color]:
            if piece_filter is None or piece.__class__.__name__ == piece_filter:
                if file_filter is None or piece.location[0] == file_filter:
                    if piece.can_move_to(location, self):
                        pieces.append(piece)
        return deepcopy(pieces)

    def who_can_capture(self, location, piece_filter=None, file_filter=None, color_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")
        pieces = []
        target = self.squares[location]
        if target is not None:
            color_filter = target.anticolor()
        for piece in self.pieces[color_filter]:
            if piece_filter is not None and piece.__class__.__name__ != piece_filter:
                continue
            if file_filter is not None and piece.location[0] not in file_filter:
                continue
            if piece.can_take(location, self):
                pieces.append(piece)
        return deepcopy(pieces)

    def check_for_checkmate(self):
        try:
            opponent_king = [x for x in self.pieces[self.antiplayer] if isinstance(x, King)][0]
        except IndexError:
            return False
        else:
            if opponent_king.is_checkmate(self):
                return True
        return False

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
                square_color = self.get_square_color(square)
                piece = self.squares[square]

                if piece is not None:
                    square_text = f'{piece} '
                    piece_color = self.black_piece_color if piece.color == 'black' else self.white_piece_color
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

    def validate_move(self, start, end):
        if end is None:
            raise self.MoveException(self, "Cannot move to nowhere. (end=None)")
        if self.squares[start] is None:
            raise self.MoveException(self, "Cannot move from an empty square.")
        piece = self.squares[start]
        if piece.color != self.active_player:
            raise self.MoveException(self, f"It's {self.active_player}'s move, you cannot move {piece.color} pieces.")
        if not self.is_valid_square_name(end):
            raise self.MoveException(self, f"Move of {piece.color} {piece.__class__.__name__} from {piece.location} to {end} is an illegal move due to {end} being out of bounds.")

    def handle_castling(self, special):
        self.castle(special)
        self.moves.append(special)
        self.enpassants = []
        if self.active_player == 'white':
            self.turn_number += 1

    def handle_enpassant(self, start, end):
        capture_rank = '5' if self.active_player == 'white' else '4'
        square_to_capture = f'{end[0]}{capture_rank}'
        captured_piece = deepcopy(self[square_to_capture])
        self[square_to_capture] = None
        self._force_move(start, end)
        self.captured_pieces[captured_piece.color].append(captured_piece)
        self[end].move_effects(end, self)

    def handle_standard_move(self, start, end):
        piece = self.squares[start]
        if not self.is_move_clear(start, end):
            raise self.MoveException(self, f"Cannot move {piece.location} through squares occupied by another piece.")
        if piece.can_move_to(end, self) and self.squares[end] is None:
            self._force_move(start, end)
            self[end].move_effects(end, self)
        elif piece.can_take(end, self) and self.squares[end] is not None:
            self.handle_capture(start, end)
        else:
            self.handle_illegal_move(piece, end)

    def handle_capture(self, start, end):
        piece = self.squares[start]
        captured_piece = self.squares[end]
        if captured_piece.color == piece.color:
            raise self.MoveException(self, f"The {piece.color} {piece.__class__.__name__} cannot capture a {piece.color} {self.squares[end].__class__.__name__} (same color).")
        self.captured_pieces[captured_piece.color].append(captured_piece)
        self.pieces[piece.anticolor()].remove(captured_piece)
        self.squares[end] = piece
        piece.location = end
        self[start] = None
        captured_piece.location = None
        piece.move_effects(end, self)
        self.enpassants = []

    def handle_illegal_move(self, piece, end):
        if self.squares[end] is None:
            raise self.MoveException(self, f"Move of {piece.color} {piece.__class__.__name__} from {piece.location} to {end} is an illegal move, as that piece cannot move to {end}")
        else:
            raise self.MoveException(self, f"Move of {piece.color} {piece.__class__.__name__} from {piece.location} to {end} is an illegal move, as that piece cannot capture the piece at {end}")

    def finalize_move(self, start, end, special, override):
        self.moves.append(f"{start} {end}")
        if not override:
            self.active_player = "black" if self.active_player == "white" else "white"
        self.check_for_checkmate()
        if self.active_player == "white":
            self.turn_number += 1

    def promote_pawn(self, location, new_type):
        piece = self[location]
        if piece is None or not isinstance(piece, Pawn):
            raise self.MoveException(self, f"Cannot promote piece at {location}, it is not a pawn")
        if not ((piece.location[1] == "8" and piece.color == 'white') or (piece.location[1] == "1" and piece.color == 'black')):
            raise self.MoveException(self, f"Can only promote pawns in the end row")
        self.squares[location] = None
        self.pieces[piece.color].remove(piece)
        new_piece = globals()[new_type](piece.color, location)
        self.add_piece(new_piece)
        self.pieces[piece.color].append(new_piece)
        self[location] = new_piece
