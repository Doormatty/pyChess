from rich.console import Console

from pieces import Pawn, Knight, Bishop, Rook, Queen, King


class Board:
    class MoveException(Exception):
        pass

    def __init__(self):
        self.console = Console()
        self.squares = {}
        self.captured = []
        self.active_player = 'white'
        self.turn_number = 0
        self.halfmove_counter = 0
        self.clear()

    def __getitem__(self, square):
        return self.squares[square]

    def __setitem__(self, square, piece):
        self.squares[square] = piece

    def move(self, start, destination):
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
        for letter in "abcdefgh":
            for number in range(1, 9):
                yield f'{letter}{number}'

    @staticmethod
    def iter_rev_square_names():
        for letter in "hgfedcba":
            for number in range(8, 0, -1):
                yield f'{letter}{number}'

    def clear(self):
        for square in self.iter_square_names():
            self[square] = None

    @staticmethod
    def get_square_color(square):
        return "black" if (ord(square[0].lower()) - ord('a') + 1 + int(square[1])) % 2 == 0 else "white"

    @staticmethod
    def get_move_distance(source, destination):
        vertical = int(destination[1]) - int(source[1])
        horizontal = abs(ord(destination[0].lower()) - ord(source[0].lower()))
        return horizontal, vertical

    @staticmethod
    def get_intermediate_squares(start, end: str):
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
        intermedes = list(self.get_intermediate_squares(start, destination))
        for square in intermedes:
            if self[square] is not None:
                return False
        return True

    def can_castle(self):
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
        return location[0] in "abcdefgh" and location[1] in "12345678"

    def export_to_fen(self):
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



