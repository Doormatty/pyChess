from rich.console import Console

from pieces import Pawn, Knight, Bishop, Rook, Queen, King


# TODO - Write function that returns a dictionary of pieces, with the values being all possible moves and captures possible by that piece.
# TODO - Write function that takes the above mentioned dictionary, and provides scores for each possible move/capture
# TODO - Handle Check and Checkmate
#


class Board:
    class MoveException(Exception):
        pass

    def __init__(self):
        """
        Initialize the chess board. Set up required variables and clear the board.
        """
        self.console = Console()
        self.squares = {}
        self.captured = []
        self.active_player = 'white'
        self.turn_number = 0
        self.halfmove_counter = 0
        self.clear()

    def __getitem__(self, square):
        """
        Overload the [] operator to access squares on the board.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        Piece object if the square is occupied else None.
        """
        return self.squares[square]

    def __setitem__(self, square, piece):
        """
        Overload the [] operator to place pieces on the board.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.
        piece (Piece): The piece object to be placed on the board.
        """
        self.squares[square] = piece

    def move(self, start, destination):
        """
        Move a piece from start square to destination square if valid.

        Parameters:
        start (str): A string in chess notation representing the start square. For example, 'd5'.
        destination (str): A string in chess notation representing the destination square. For example, 'e7'.

        Raises:
        MoveException: If the move is not valid due to reasons like moving opponent's pieces, illegal move path,
        casting check on own king etc.
        """
        if self[start] is None:
            raise self.MoveException(f"Cannot move from an empty square.")
        piece = self[start]
        if self[start].color != self.active_player:
            raise self.MoveException(f"It's {self.active_player}'s move, you cannot move {piece.color} pieces.")
        if not self.is_move_clear(start, destination):
            raise self.MoveException(f"Cannot move {piece.location} through squares occupied by another piece.")
        if not self._boundry_check(destination):
            raise self.MoveException(f"Move of {piece.color} {self.__class__.__name__} from {piece.location} to {destination} is an illegal move due to {destination} being out of bounds.")
        # Are we only moving, and not capturing?
        if piece.can_move_to(destination) and self[destination] is None:
            self[start] = None
            piece.location = destination
            self[destination] = piece
            piece.has_moved = True
            piece.move_effects(destination)
        # Are we moving and capturing?
        elif piece.can_take(destination) and self[destination] is not None:
            if self[destination].color == piece.color:
                raise self.MoveException(f"Cannot capture piece of same color.")
            # Remove the taken piece's location, add it to the captured list
            self[destination].location = None
            self.captured.append(self[destination])
            # Set the piece's position to where the taken piece was
            self[destination] = piece
            self[start] = None
            piece.location = destination
            piece.has_moved = True
            # reset the halfmove counter
            self.halfmove_counter = 0
            piece.move_effects(destination)
        else:
            raise self.MoveException(f"Move of {piece.color} {self.__class__.__name__} from {piece.location} to {destination} is an illegal move")
        self.active_player = "black" if self.active_player == "white" else "white"

    @staticmethod
    def iter_square_names():
        """
        Iterate over all squares of the board from left to right and top to bottom.

        Yields:
        str: The square in chess notation, for example, 'a1', 'a2'...'h8'.
        """
        for letter in "abcdefgh":
            for number in range(1, 9):
                yield f'{letter}{number}'

    @staticmethod
    def iter_rev_square_names():
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
        for square in self.iter_square_names():
            self[square] = None

    @staticmethod
    def get_square_color(square):
        """
        Check the color of the square, using the board's 8x8 grid and the chess rule of alternation.

        Parameters:
        square (str): A string in chess notation representing the square. For example, 'd5'.

        Returns:
        str: "black" if the square is black, "white" if the square is white.
        """
        return "black" if (ord(square[0].lower()) - ord('a') + 1 + int(square[1])) % 2 == 0 else "white"

    @staticmethod
    def get_move_distance(source, destination):
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
    def get_intermediate_squares(start, end: str):
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

    def is_move_clear(self, start, destination):
        """
        Check if a move from start square to destination square is clear, i.e., there are no other pieces blocking the way.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        destination (str): The ending square in chess notation, for example, 'e7'.

        Returns:
        bool: True if path is clear, False otherwise.
        """
        intermedes = list(self.get_intermediate_squares(start, destination))
        for square in intermedes:
            if self[square] is not None:
                return False
        return True

    def can_castle(self):
        """
        Check if either of the kings can still legally castle.

        Returns:
        str: A string representing the castling availability. 'KQkq' means that both kings can castle to both sides.
        '-' means no king can castle anymore.
        """
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

    @staticmethod
    def _boundry_check(location):
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
                else:
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
        self.clear()
        self.turn_number = 1
        for square in self.iter_square_names():
            if square[1] in ('3', '4', '5', '6'):
                self[square] = None
            elif square[1] == '2':
                self[square] = Pawn('white', location=square, board=self)
            elif square[1] == '7':
                self[square] = Pawn('black', location=square, board=self)

            if square[1] in ('1', '8'):
                if square[1] == '1':
                    color = 'white'
                else:
                    color = 'black'

                if square[0] in ('a', 'h'):
                    self[square] = Rook(color=color, location=square, board=self)
                elif square[0] in ('b', 'g'):
                    self[square] = Knight(color=color, location=square, board=self)
                elif square[0] in ('c', 'f'):
                    self[square] = Bishop(color=color, location=square, board=self)

                elif square[0] == 'd':
                    if color == 'white':
                        self[square] = King(color=color, location=square, board=self)
                    else:
                        self[square] = Queen(color=color, location=square, board=self)
                elif square[0] == 'e':
                    if color == 'white':
                        self[square] = Queen(color=color, location=square, board=self)
                    else:
                        self[square] = King(color=color, location=square, board=self)

    def print(self):
        for number in range(8, 0, -1):
            for letter in "abcdefgh":
                square = f'{letter}{number}'
                square_color = self.get_square_color(square)
                piece = self.squares[square]
                if piece is None:
                    self.console.print('  ', end='', style="red on bright_white" if square_color == "black" else "red on white")
                else:
                    if square_color == "black":
                        square_color = "bright_white"
                    self.console.print(f'{piece} ', end='', style=f"black on {square_color}")
            print('')
