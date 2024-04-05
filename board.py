import re
from collections import defaultdict
from collections.abc import Iterator
from functools import cache

from rich.console import Console
from rich.text import Text

from pieces import Pawn, Knight, Bishop, Rook, Queen, King, Piece


# TODO - Write function that returns a dictionary of pieces, with the values being all possible moves and captures possible by that piece.
# TODO - Write function that takes the above mentioned dictionary, and provides scores for each possible move/capture
# TODO - Handle Check and Checkmate

class Board:
    class MoveException(Exception):
        pass
        # def __init__(self, message, highlights=None):
        #     super().__init__(message)
        #     self.highlights = highlights

    _precomputed_square_names = [f'{letter}{number}' for letter in 'abcdefgh' for number in range(1, 9)]

    def __init__(self):
        """
        Initialize the chess board. Set up required variables and clear the board.
        """
        self.console = Console()
        self.pieces = {"white": [], "black": []}
        self.squares: defaultdict[str, None | Piece] = defaultdict(lambda: None)
        self.captured_pieces = {"white": [], "black": []}
        self.active_player = 'white'
        self.turn_number = 0
        self.halfmove_counter = 0
        self.enpassants = []
        self.castling = []
        self.black_square_color = 'white'
        self.white_square_color = 'bright_white'
        self.black_piece_color = 'blue'
        self.white_piece_color = 'green'
        self.highlight_color = 'red'

    def __getitem__(self, square) -> Piece | None:
        """
        Overload the [] operator to access squares on the board.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        Piece object if the square is occupied else None.
        """
        return self.squares[square]

    def __setitem__(self, square: str, piece: Piece):
        """
        Overload the [] operator to place pieces on the board.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.
        piece (Piece): The piece object to be placed on the board.
        """
        self.squares[square] = piece

    def add_piece(self, piece: Piece):
        color = piece.color
        location = piece.location
        if self.squares[location] is not None:
            raise self.MoveException(f"Cannot add {piece} to {location}, already occupied by {self.squares[location]}")
        self.pieces[color].append(piece)
        self.squares[location] = piece

    def _force_move(self, start: str, destination: str):
        piece = self.squares[start]
        self.squares[start] = None
        piece.location = destination
        self.squares[destination] = piece
        piece.has_moved = True
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
            self.castle(self.active_player, start)
            return

        if destination is None:
            raise self.MoveException(f"Cannot move to nowhere. (destination=None)")

        if self.squares[start] is None:
            raise self.MoveException(f"Cannot move from an empty square.")
        piece = self.squares[start]
        if piece.color != self.active_player:
            raise self.MoveException(f"It's {self.active_player}'s move, you cannot move {piece.color} pieces.")
        if not override:
            if not self.is_move_clear(start, destination):
                raise self.MoveException(f"Cannot move {piece.location} through squares occupied by another piece.")
        if not self._boundry_check(destination):
            raise self.MoveException(f"Move of {piece.color} {self.__class__.__name__} from {piece.location} to {destination} is an illegal move due to {destination} being out of bounds.")
        # Are we only moving, and not capturing?
        if piece.can_move_to(destination) and self.squares[destination] is None:
            self._force_move(start, destination)
        # Are we moving and capturing?
        elif piece.can_take(destination) and self.squares[destination] is not None:

            if self.squares[destination].color == piece.color:
                raise self.MoveException(f"Cannot capture piece of same color.")
            # Remove the taken piece's location, add it to the captured list
            self.captured_pieces[piece.anticolor()].append(self[destination])
            # Remove the taken piece from the list
            self.pieces[piece.anticolor()].remove(self[destination])

            # Set the piece's position to where the taken piece was
            self.squares[destination] = piece
            self.squares[start] = None
            piece.location = destination
            piece.has_moved = True
            # reset the halfmove counter
            self.halfmove_counter = 0
            piece.move_effects(destination)
        else:
            raise self.MoveException(f"Move of {piece.color} {piece.__class__.__name__} from {piece.location} to {destination} is an illegal move")
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
    @cache
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
    @cache
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
    @cache
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

    def castle(self, color: str, move: str):
        if move == "O-O":
            if color == "white":
                self._force_move("e1", "g1")
                self._force_move("h1", "f1")
                self.active_player = "black"
            else:
                self._force_move("e8", "g8")
                self._force_move("h8", "f8")
                self.active_player = "white"
        elif move == "O-O-O":
            if color == "white":
                self._force_move("e1", "c1")
                self._force_move("a1", "e1")
                self.active_player = "black"
            else:
                self._force_move("e8", "c8")
                self._force_move("a8", "e8")
                self.active_player = "white"

    def can_castle(self) -> str:
        """
        Check if either of the kings can still legally castle.

        Returns:
        str: A string representing the castling availability. 'KQkq' means that both kings can castle to both sides.
        '-' means no king can castle anymore.
        """

        # TODO - Currently this doesn't check if any of the squares are under attack
        retval = ""
        if self['d1'] is not None and not self['d1'].has_moved:
            if self['a1'] is not None and not self['a1'].has_moved:
                retval += "K"
            if self['h1'] is not None and not self['h1'].has_moved:
                retval += "Q"
        if self['e8'] is not None and not self['e8'].has_moved:
            if self['h8'] is not None and not self['h8'].has_moved:
                retval += "k"
            if self['a8'] is not None and not self['a8'].has_moved:
                retval += "q"
        if retval == "":
            retval = '-'
        return retval

    def compact_move(self, move: str):
        parsed_move = self.parse_move(move)
        expanded_move = self.expand_move(parsed_move)
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
                print(e)
            print(f"{self.active_player}: {expanded_move[0]} to {expanded_move[1]}")

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

    def expand_move(self, parsed_move) -> tuple[str, str | None]:
        #TODO - Need to add capturing when elif len(source_square) == 1: isn' true!!!
        possibles = None
        if parsed_move['king_castle'] or parsed_move['queen_castle']:
            return parsed_move, None
        source_square = parsed_move['source_square']
        if source_square is None:
            possibles = self.who_can_move_to(location=parsed_move['dest_square'], piece_filter=parsed_move['source_type'].__qualname__)
        elif parsed_move['dest_square'] is None:
            possibles = self.who_can_move_to(location=parsed_move['source_square'], piece_filter=parsed_move['source_type'].__qualname__)
        elif len(source_square) == 1:
            if source_square.isalpha():
                if parsed_move['capture']:
                    possibles = self.who_can_capture(location=parsed_move['dest_square'], file_filter=source_square, piece_filter=parsed_move['source_type'].__qualname__)
                else:
                    possibles = self.who_can_move_to(location=parsed_move['dest_square'], file_filter=source_square, piece_filter=parsed_move['source_type'].__qualname__)

        if possibles is None or len(possibles) == 0:
            raise self.MoveException(f"No possibilities were found for {parsed_move['move']}")
        if len(possibles) > 1:
            raise self.MoveException(f"Move {parsed_move['move']} is not sufficiently described. {len(possibles)} possibilities {possibles} were found")
        source_square = possibles[0].location
        return source_square, parsed_move['dest_square']

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
        fen += f"{' w' if self.turn_number % 2 == 1 else ' b'} {self.can_castle()}"
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
            if square[1] in ('3', '4', '5', '6'):
                self.squares[square] = None
                continue
            elif square[1] == '2':
                self.add_piece(piece=Pawn('white', location=square, board=self))
                continue
            elif square[1] == '7':
                self.add_piece(piece=Pawn('black', location=square, board=self))
                continue

            if square[1] in ('1', '8'):
                if square[1] == '1':
                    color = 'white'
                else:
                    color = 'black'

                if square[0] in ('a', 'h'):
                    self.add_piece(piece=Rook(color, location=square, board=self))
                elif square[0] in ('b', 'g'):
                    self.add_piece(piece=Knight(color, location=square, board=self))
                elif square[0] in ('c', 'f'):
                    self.add_piece(piece=Bishop(color, location=square, board=self))

                elif square[0] == 'd':
                    if color == 'white':
                        self.add_piece(piece=Queen(color, location=square, board=self))
                    else:
                        self.add_piece(piece=Queen(color, location=square, board=self))
                elif square[0] == 'e':
                    if color == 'white':
                        self.add_piece(piece=King(color, location=square, board=self))
                    else:
                        self.add_piece(piece=King(color, location=square, board=self))

    def who_can_move_to(self, location, color=None, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")
        if color is None:
            color = self.active_player
        pieces = []
        for piece in self.pieces[color]:
            if piece_filter is not None and piece.__class__.__name__ != piece_filter:
                continue
            if file_filter is not None and piece.location[0] != file_filter:
                continue
            if piece.can_move_to(location):
                pieces.append(piece)
        return pieces

    def who_can_capture(self, location, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")
        pieces = []
        target = self.squares[location]
        if target is None:
            raise self.MoveException(f"Nothing to capture at {location}!")
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

    def print(self, highlight=None) -> None:
        self.console.print(self.create_board_text(highlight))

    def create_board_text(self, highlight=None) -> Text:
        if isinstance(highlight, str):
            highlight = [highlight]

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

                if highlight is not None and square in highlight:
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
