from functools import cache


class Piece:
    class MoveException(Exception):
        pass

    def __init__(self, color, location, board):
        if isinstance(location, int):
            self._location = self.index_to_square(location)
        else:
            self._location = location
        self.int_vert = int(self._location[1])
        self.int_horz = ord(self._location[0].lower())
        self.color = color
        self.board = board
        self.points = None
        self.has_moved = False

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value
        try:
            self.int_vert = int(self._location[1])
            self.int_horz = ord(self._location[0].lower())
        except TypeError:
            print('')

    @cache
    def get_move_distance(self, destination):
        if isinstance(destination, str):
            vertical = int(destination[1]) - self.int_vert
            horizontal = self.int_horz - ord(destination[0].lower())
        else:
            vertical = self.int_vert - destination.int_vert
            horizontal = self.int_horz - destination.int_horz
        return horizontal, vertical

    @staticmethod
    @cache
    def index_to_square(number):
        if not 0 <= number <= 63:
            raise Piece.MoveException(f'{number} a valid index.')
        return f"{chr(ord('a') + (number % 8))}{8 - (number // 8)}"

    def anticolor(self):
        if self.color == "black":
            return "white"
        else:
            return "black"

    def can_move_to(self, location):
        raise NotImplementedError

    def can_take(self, location):
        return self.can_move_to(location) and self.board[location] is not None and self.board[location].color == self.anticolor()

    def get_all_possible_moves(self):
        possible_moves = []
        for square in self.board.iter_square_names():
            if self.can_move_to(square) or self.can_take(square):
                possible_moves.append(square)
        return possible_moves

    def move_effects(self, location):
        pass


class Pawn(Piece):
    def __init__(self, color, location, board):
        if isinstance(location, int):
            location = self.index_to_square(location)
        super().__init__(color=color, location=location, board=board)
        self.points = 1
        self.starting_position = None
        if location[1] in ('2', '7'):
            self.starting_position = True

    def __str__(self):
        if self.color == "black":
            return "♙"
        elif self.color == "white":
            return "♟"

    def __repr__(self):
        return f"Pawn({self.color=}, {self.location=})"

    def _enpassant_squares(self):
        h = self.location[0]
        v = int(self.location[1])
        if self.color == "black":
            if h == "a":
                return 'b6',
            elif h == "h":
                return 'g6',
            else:
                return f"{chr(ord(h) - 1)}{v + 1}", f"{chr(ord(h) + 1)}{v + 1}"
        else:
            if h == "a":
                return 'b3',
            elif h == "h":
                return 'g3',
            else:
                return f"{chr(ord(h) - 1)}{v - 1}", f"{chr(ord(h) + 1)}{v - 1}"

    def move_effects(self, location):
        self.starting_position = False
        self.board.halfmove_counter = 0
        possible_enpassants = []
        for square in self._enpassant_squares():
            if self.board[square] is not None and self.board[square].__class__.__name__ == "Pawn" and self.board[square].color == self.anticolor():
                possible_enpassants.append(square)
        if possible_enpassants:
            self.board.enpassants = possible_enpassants

    def can_move_to(self, location):
        move_distance = self.get_move_distance(location)
        if move_distance[0] != 0:
            return False
        if not self.board.is_move_clear(self.location, location):
            return False
        color = 1 if self.color == "white" else -1
        if move_distance[1] == 1 * color or (move_distance[1] == 2 * color and self.starting_position):
            return True

    def can_take(self, location):
        move_distance = self.get_move_distance(location)
        if move_distance[0] in (1,-1) and ((move_distance[1] == 1 and self.color == "white") or (move_distance[1] == -1 and self.color == "black")):
            return True
        return False


class Knight(Piece):
    def __init__(self, color, location, board):
        super().__init__(color=color, location=location, board=board)
        self.points = 3

    def __str__(self):
        if self.color == "black":
            return "♘"
        elif self.color == "white":
            return "♞"

    def __repr__(self):
        return f"Knight({self.color=}, {self.location=})"

    def can_move_to(self, location):
        move_distance = self.get_move_distance(location)
        return (move_distance[0] in (1, -1) and move_distance[1] in (2, -2)) or (move_distance[0] in (2, -2) and move_distance[1] in (1, -1))


class Bishop(Piece):
    def __init__(self, color, location, board):
        super().__init__(color=color, location=location, board=board)
        self.points = 3

    def __str__(self):
        if self.color == "black":
            return "♗"
        elif self.color == "white":
            return "♝"

    def __repr__(self):
        return f"Bishop({self.color=}, {self.location=})"

    def can_move_to(self, location):
        if not self.board.is_move_clear(self.location, location):
            return False
        move_distance = self.get_move_distance(location)
        return abs(move_distance[0]) == abs(move_distance[1])


class Rook(Piece):
    def __init__(self, color, location, board):
        super().__init__(color=color, location=location, board=board)
        self.points = 5

    def __str__(self):
        if self.color == "black":
            return "♖"
        elif self.color == "white":
            return "♜"

    def __repr__(self):
        return f"Rook({self.color=}, {self.location=})"

    def can_move_to(self, location):
        if not self.board.is_move_clear(self.location, location):
            return False
        move_distance = self.get_move_distance(location)
        return move_distance[0] == 0 or move_distance[1] == 0


class Queen(Piece):
    def __init__(self, color, location, board):
        super().__init__(color=color, location=location, board=board)
        self.points = 9

    def __str__(self):
        if self.color == "black":
            return "♕"
        elif self.color == "white":
            return "♛"

    def __repr__(self):
        return f"Queen({self.color=}, {self.location=})"

    def can_move_to(self, location):
        if not self.board.is_move_clear(self.location, location):
            return False
        move_distance = self.get_move_distance(location)
        return abs(move_distance[0]) == abs(move_distance[1]) or (move_distance[0] == 0 or move_distance[1] == 0)


class King(Piece):
    def __init__(self, color, location, board):
        super().__init__(color=color, location=location, board=board)
        self.points = 100

    def __str__(self):
        if self.color == "black":
            return "♔"
        elif self.color == "white":
            return "♚"

    def __repr__(self):
        return f"King({self.color=}, {self.location=})"

    def is_checkmate(self):
        all_adjacent_squares_blocked = True
        for y in (-1, 0, 1):
            for x in (-1, 0, 1):
                if x == 0 and y == 0:  # Skip the square where the king currently is
                    continue
                target_square = f"{chr(ord(self.location[0]) + x)}{(int(self.location[1]) + y)}"
                if not self.board._boundry_check(target_square):
                    continue
                if self.can_move_to(target_square):
                    return False
                elif self.board[target_square] is None or self.board[target_square].color != self.color:
                    all_adjacent_squares_blocked = False
        return all_adjacent_squares_blocked

    def can_move_to(self, location):
        move_distance = self.get_move_distance(location)
        if abs(move_distance[0]) > 1 and abs(move_distance[1]) > 1:
            return False
        if location is None:
            raise ValueError("Location cannot be None")
        for piece in self.board.pieces[self.anticolor()]:
            if isinstance(piece, King):
                continue
            if piece.can_take(location):
                return False
        return True
