import logging
import re
from collections import defaultdict
from collections.abc import Iterator
from copy import deepcopy

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from pieces import Pawn, Knight, Bishop, Rook, Queen, King, Piece


# TODO - Write function that returns a dictionary of pieces, with the values being all possible moves and captures possible by that piece.
# TODO - Write function that takes the above mentioned dictionary, and provides scores for each possible move/capture
# TODO - Handle Check and Checkmate

class Board:
    class MoveException(Exception):
        def __init__(self, board: 'Board', message: str, highlights: list[str] | str | None = None, *args):
            super().__init__(message, *args)
            self.board = board
            self.highlights = highlights
            self.message = message

        def rich_exception(self):
            self.board.console.print(self.message, style="bold red")
            self.board.print(highlights=self.highlights)
            for num, move in enumerate(self.board.moves):
                self.board.console.print(f"{num + 1}. {move}", style="bold green")

    class TempMove:
        def __init__(self, board: 'Board'):
            self.undo_state = dict()
            self.attrs = ('turn_number', 'halfmove_counter', 'enpassants', 'castling', 'active_player', 'moves')
            self.deepattrs = ('squares', 'pieces')
            self.board = board

        def __enter__(self) -> 'Board.TempMove':
            for attr in self.attrs:
                self.undo_state[attr] = getattr(self.board, attr)
            for attr in self.deepattrs:
                self.undo_state[attr] = deepcopy(getattr(self.board, attr))
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            for attr in self.attrs:
                setattr(self.board, attr, self.undo_state[attr])
            for attr in self.deepattrs:
                setattr(self.board, attr, self.undo_state[attr])
            return self

    _precomputed_square_names = [f'{letter}{number}' for letter in 'abcdefgh' for number in range(1, 9)]

    def __init__(self):
        """
        Initialize the chess board. Set up required variables and clear the board.
        """
        self.console = Console(width=160)
        self.pieces = {"white": [], "black": []}
        self.squares: defaultdict[str, None | Piece] = defaultdict(lambda: None)
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
        logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

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

    def add_piece(self, piece: Piece):
        color = piece.color
        location = piece.location
        if self[location] is not None:
            raise self.MoveException(self, f"Cannot add {piece} to {location}, already occupied by {self.squares[location]}")
        self.pieces[color].append(piece)
        self[location] = piece

    def _force_move(self, start: str, destination: str):
        piece = self[start]
        self[start] = None
        self[destination] = piece
        piece.move_effects(destination)

    def move(self, start, destination=None, override=False):
        """
        Move a piece from start square to destination square if valid.

        Parameters:
        start (str): A string in chess notation representing the start square. For example, 'd5'.
        destination (str): A string in chess notation representing the destination square. For example, 'e7'.

        Raises:
        MoveException: If the move is not valid due to reasons like moving opponent's pieces, illegal move path,
        casting check on own king etc.
        """
        if start in ("O-O", "O-O-O"):
            self.castle(start)
            return

        if destination is None:
            raise self.MoveException(self, f"Cannot move to nowhere. (destination=None)")

        if self.squares[start] is None:
            raise self.MoveException(self, f"Cannot move from an empty square.")
        piece = self.squares[start]
        if piece.color != self.active_player:
            raise self.MoveException(self, f"It's {self.active_player}'s move, you cannot move {piece.color} pieces.")
        if not override:
            if not self.is_move_clear(start, destination):
                raise self.MoveException(self, f"Cannot move {piece.location} through squares occupied by another piece.")
        if not self._boundry_check(destination):
            raise self.MoveException(self, f"Move of {piece.color} {self.__class__.__name__} from {piece.location} to {destination} is an illegal move due to {destination} being out of bounds.")
        # Are we only moving, and not capturing?
        if piece.can_move_to(destination) and self.squares[destination] is None:
            self._force_move(start, destination)
        # Are we moving and capturing?
        elif piece.can_take(destination) and self.squares[destination] is not None:

            if self.squares[destination].color == piece.color:
                raise self.MoveException(self, f"The {piece.color} {piece.__class__.__name__} cannot capture a {piece.color} {self.squares[destination].__class__.__name__} (same color).")
            # Remove the taken piece's location, add it to the captured list
            self.captured_pieces[piece.anticolor()].append(self[destination])
            # Remove the taken piece from the list
            self.pieces[piece.anticolor()].remove(self[destination])

            # Set the piece's position to where the taken piece was
            self[destination] = piece
            self.squares[start] = None
            piece.move_effects(destination)
        else:
            raise self.MoveException(self, f"Move of {piece.color} {piece.__class__.__name__} from {piece.location} to {destination} is an illegal move")
        if not override:
            self.active_player = "black" if self.active_player == "white" else "white"
        self.check_for_checkmate()

    def iter_square_names(self) -> Iterator[str]:
        """
        Iterate over all squares of the board from left to right and top to bottom.

        Yields:
        str: The square in chess notation, for example, 'a1', 'a2'...'h8'.
        """
        return iter(self._precomputed_square_names)

    @staticmethod
    def iter_rev_square_names() -> Iterator[str]:
        """
        Iterate over all squares of the board from right to left and bottom to top.

        Yields:
        str: The square in chess notation, for example, 'h8', 'h7'...'a1'.
        """
        for letter in "hgfedcba":
            for number in range(8, 0, -1):
                yield f'{letter}{number}'

    def clear(self):
        """
        Clear the board.
        """
        self.squares = defaultdict(lambda: None)

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
    def get_move_distance(source: str, destination: str) -> tuple[int, int]:
        """
        Computes the vertical and horizontal distance between two squares.

        Parameters:
        source (str): The starting square in chess notation, for example, 'd5'.
        destination (str): The ending square in chess notation, for example, 'e7'.

        Returns:
        A tuple of (horizontal_distance, vertical_distance).
        """
        vertical = int(destination[1]) - int(source[1])
        horizontal = abs(ord(destination[0].lower()) - ord(source[0].lower()))
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

    def is_move_clear(self, start: str, destination: str) -> bool:
        """
        Check if a move from start square to destination square is clear, i.e., there are no other pieces blocking the way.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        destination (str): The ending square in chess notation, for example, 'e7'.

        Returns:
        bool: True if path is clear, False otherwise.
        """
        for square in self.get_intermediate_squares(start, destination):
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
            else:
                self._force_move("e8", "g8")
                self._force_move("h8", "f8")
        elif move == "O-O-O":
            if not can_castle[color]['queenside']:
                raise self.MoveException(self, f"{color} cannot castle Queenside.")
            if color == "white":
                self._force_move("e1", "c1")
                self._force_move("a1", "e1")
            else:
                self._force_move("e8", "c8")
                self._force_move("a8", "e8")
        self.halfmove_counter += 1
        self.active_player = 'white' if self.active_player == 'black' else 'black'

    def can_castle(self) -> dict:
        retval = {'white': {}, 'black': {}}
        if self['e1'] is not None and not self['e1'].has_moved:
            retval['white']['queenside'] = self['a1'] is not None and not self['a1'].has_moved and self.who_can_capture('e1') is None and self.who_can_capture('d1') is None and self.who_can_capture('c1') is None and self.who_can_capture('b1')
            retval['white']['kingside'] = self['h1'] is not None and not self['h1'].has_moved and self.who_can_capture('e1') is None and self.who_can_capture('f1') is None and self.who_can_capture('g1') is None
        if self['e8'] is not None and not self['e8'].has_moved:
            retval['black']['queenside'] = self['a8'] is not None and not self['a8'].has_moved and self.who_can_capture('e8') is None and self.who_can_capture('d8') is None and self.who_can_capture('c8') is None and self.who_can_capture('b8') is None
            retval['black']['kingside'] = self['h8'] is not None and not self['h8'].has_moved and self.who_can_capture('e8') is None and self.who_can_capture('f8') is None and self.who_can_capture('g8') is None
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

    def compact_move(self, move: str):
        parsed_move = self.parse_move(move)
        logging.debug(f"Parsed {move} into {parsed_move}")
        expanded_move = self.expand_move(parsed_move)
        logging.debug(f"Expanded move into {expanded_move[0]} --> {expanded_move[1]}")
        if move in ("O-O", "O-O-O"):
            self.move(move)
            if move == "O-O-O":
                print(f"{self.active_player}: castles Queenside")
            else:
                print(f"{self.active_player}: castles Kingside")
        else:
            try:
                self.move(expanded_move[0], expanded_move[1])
            except self.MoveException as e:
                logging.error(e)
                # print(e)
            logging.info(f"Executed {self.active_player}: {expanded_move[0]} to {expanded_move[1]}")

    @staticmethod
    def parse_move(move: str) -> dict:
        pattern = r'((?P<source_type>[KQNBR])?(?P<source_square>[a-h][1-8]?)?(?P<capture>x)?(?P<dest_type>[KQNBR])?(?P<dest_square>[a-h][1-8])(?P<check>\+)?)?(?P<kscastle>O-O)?(?P<qscastle>O-O-O)?(?P<checkmate>#)?'
        parts = re.match(pattern, move)
        type_dict = {'K': King, 'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight}
        return {'move': move,
                'source_type': type_dict[parts['source_type']] if parts['source_type'] is not None else Pawn,
                'dest_type': type_dict[parts['dest_type']] if parts['dest_type'] is not None else None,
                'source_square': parts['source_square'],
                'dest_square': parts['dest_square'],
                'capture': True if parts['capture'] else False,
                'check': True if parts['check'] else False,
                'checkmate': True if parts['checkmate'] else False,
                'king_castle': True if parts['kscastle'] else False,
                'queen_castle': True if parts['qscastle'] else False}

    def does_move_cause_self_check(self, source, destination):
        with self.TempMove(self):
            self._force_move(source, destination)
            return self.is_king_in_check(self.active_player)

    def is_king_in_check(self, player):
        king = [piece for piece in self.pieces[player] if piece.__class__.__name__ == 'King'][0]
        attackers = self.who_can_capture(king.location)
        if attackers:
            return True
        return False

    def expand_move(self, parsed_move) -> tuple[str, str | None]:
        if parsed_move['king_castle'] or parsed_move['queen_castle']:
            return parsed_move, None

        source_square = parsed_move['source_square']
        dest_square = parsed_move['dest_square']
        piece_filter = parsed_move['source_type'].__qualname__

        if source_square is None or dest_square is None:
            location = source_square or dest_square
            possibles = self.who_can_move_to(location=location, piece_filter=piece_filter)
        else:
            if parsed_move['capture']:
                possibles = self.who_can_capture(location=dest_square, piece_filter=piece_filter)
            else:
                possibles = self.who_can_move_to(location=dest_square, piece_filter=piece_filter)

            if len(source_square) == 1 and source_square.isalpha():
                possibles = [p for p in possibles if p.location[0] == source_square]

        if not possibles:
            raise self.MoveException(self, f"No possibilities were found for {parsed_move['move']} in {parsed_move} even before self-check detection!")
        possible_count = len(possibles)
        possibles = [possible for possible in possibles if self.does_move_cause_self_check(possible.location, dest_square)]
        logging.info(f"Removed {len(possibles) - possible_count} possible moves due to self-check.")
        if not possibles:
            raise self.MoveException(self, f"No possibilities were found for {parsed_move['move']} in {parsed_move} after self-check check.")
        if len(possibles) > 1:
            raise self.MoveException(self, f"{self.active_player}'s move {parsed_move['move']} is inadequately described - {len(possibles)} possibilities {possibles} were found")

        source_square = possibles[0].location
        return source_square, dest_square

    @staticmethod
    def _boundry_check(location: str) -> bool:
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
                self.add_piece(piece=Pawn('white', location=square, board=self))
            elif row == '7':
                self.add_piece(piece=Pawn('black', location=square, board=self))
            elif row in ('1', '8'):
                color = 'white' if row == '1' else 'black'

                if col in ('a', 'h'):
                    self.add_piece(piece=Rook(color, location=square, board=self))
                elif col in ('b', 'g'):
                    self.add_piece(piece=Knight(color, location=square, board=self))
                elif col in ('c', 'f'):
                    self.add_piece(piece=Bishop(color, location=square, board=self))
                elif col == 'd':
                    self.add_piece(piece=Queen(color, location=square, board=self))
                elif col == 'e':
                    self.add_piece(piece=King(color, location=square, board=self))

    def who_can_move_to(self, location, color=None, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")

        color = color or self.active_player
        pieces = []
        for piece in self.pieces[color]:
            if piece_filter is None or piece.__class__.__name__ == piece_filter:
                if file_filter is None or piece.location[0] == file_filter:
                    if piece.can_move_to(location):
                        pieces.append(piece)
        return pieces

    def who_can_capture(self, location, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")
        pieces = []
        target = self.squares[location]
        if target is None:
            raise self.MoveException(self, f"Nothing to capture at {location}!")
        color = target.anticolor()

        for piece in self.pieces[color]:
            if piece_filter is not None and piece.__class__.__name__ != piece_filter:
                continue
            if file_filter is not None and piece.location[0] not in file_filter:
                continue
            if piece.can_take(location):
                pieces.append(piece)
        return pieces

    def check_for_checkmate(self):
        oppoenent_pieces = self.pieces["black" if self.active_player == "white" else "white"]
        opponent_king = [x for x in oppoenent_pieces if isinstance(x, King)][0]
        if opponent_king.is_checkmate():
            print("!!!!CHECKMATE!!!!")

    def print(self, highlights: str | list[str] | None = None) -> None:
        self.console.print(self.create_board_text(highlights))

    def create_board_text(self, highlights: str | list[str] = None) -> Text:
        if isinstance(highlights, str):
            highlights = [highlights]

        # Add file labels at the top
        board_text = Text("  a b c d e f g h\n", style="bold")

        for number in range(8, 0, -1):
            # Add rank label at the start of each line
            board_text.append(f"{number} ", style="bold")

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
        board_text.append("  a b c d e f g h", style="bold")

        return board_text
