from utils import Color, Location


class Piece:
    class MoveException(Exception):
        pass

    def __init__(self, color, location):
        if isinstance(location, str):
            location = Location(location)
        self._location = location
        if location is not None:
            self.int_vert = location.rank
            self.int_horz = location.int_file
        self.color = color
        self.points = None
        self.has_moved = False

    def __deepcopy__(self, memo):
        result = self.__class__(self.color, self.location)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k not in ['_location', 'int_vert', 'int_horz']:
                setattr(result, k, v)
        return result

    def string(self):
        return f'{self.color.value} {self.__class__.__name__}'

    def __eq__(self, other):
        return self.color == other.color and self.location == other.location

    def __ne__(self, other):
        return self.color != other.color or self.location != other.location

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if value is None:
            self._location = None
            self.int_horz = None
            self.int_vert = None
        else:
            if isinstance(value, str):
                value = Location(value)
            self._location = value
            self.int_vert = value.rank
            self.int_horz = value.int_file

    def anticolor(self):
        if self.color == Color.BLACK:
            return Color.WHITE
        else:
            return Color.BLACK

    def can_move_to(self, location: str | Location, game):
        raise NotImplementedError

    def can_take(self, location: str | Location, game) -> bool:
        result = self.can_move_to(location, game)

        # and board[location] is not None and board[location].color == self.anticolor())
        return result

    def get_all_possible_moves(self, board) -> list[Location]:
        possible_moves = []
        for square in board.iter_square_names():
            if self.can_move_to(square, board) or self.can_take(square, board):
                possible_moves.append(square)
        return possible_moves

    def move_effects(self, start: Location, end: Location, game):
        game.board.enpassants = []


class Pawn(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 1

    def __str__(self):
        if self.color == Color.BLACK:
            return "♙"
        elif self.color == Color.WHITE:
            return "♟"

    def __repr__(self):
        return f"Pawn('{self.color}', '{self.location}')"

    def _enpassant_squares(self) -> tuple[str] | tuple[str, str] | list:
        if self.has_moved:
            return []
        h = self.location[0]
        v = int(self.location[1])
        if self.color == Color.BLACK:
            if h == "a":
                return 'b6',
            elif h == "h":
                return 'g6',
            else:
                return f"{chr(ord(h) - 1)}{v - 1}", f"{chr(ord(h) + 1)}{v - 1}"
        else:
            if h == "a":
                return 'b3',
            elif h == "h":
                return 'g3',
            else:
                return f"{chr(ord(h) - 1)}{v + 1}", f"{chr(ord(h) + 1)}{v + 1}"

    def move_effects(self, start: Location | str, end: Location, game):
        if isinstance(start, str):
            start = Location(start)
        if isinstance(end, str):
            end = Location(end)
        if self.location is None:
            return
        game.halfmove_counter = 0
        if end is not None and start - end in ((0, 2), (0, -2)):
            if self.color == Color.BLACK:
                game.enpassants = f"{self.location[0]}{self.int_vert + 1}"
            else:
                game.enpassants = f"{self.location[0]}{self.int_vert - 1}"
        else:
            game.enpassants = None
        self.has_moved = True

    def can_move_to(self, location: Location | str, game):
        if isinstance(location, str):
            location = Location(location)
        if self.location is None:
            return False
        move_distance = location - self.location
        if move_distance[0] != 0:
            return False
        try:
            if not game.board.is_move_clear(self.location, location):
                return False
        except AttributeError as e:
            print('')
        color = 1 if self.color == Color.WHITE else -1
        if move_distance[1] == (1 * color):
            return True
        if move_distance[1] == (2 * color) and not self.has_moved:
            return True
        return False

    def can_take(self, location: Location, game):
        if self.location is None:
            raise self.MoveException("Why are we trying to take a piece that doesn't have a location?")
        move_distance = self.location - location
        if move_distance[0] in (1, -1) and ((move_distance[1] == -1 and self.color == Color.WHITE) or (move_distance[1] == 1 and self.color == Color.BLACK)):
            return True
        if game.enpassants is not None and location in game.enpassants and game.board[location].__class__.__name__ == "Pawn":
            return True
        return False


class Knight(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 3

    def __str__(self):
        if self.color == Color.BLACK:
            return "♘"
        elif self.color == Color.WHITE:
            return "♞"

    def __repr__(self):
        return f"Knight('{self.color}', '{self.location}')"

    def can_move_to(self, location, game):
        if self.location is None:
            return False
        move_distance = self.location - location
        return (move_distance[0] in (1, -1) and move_distance[1] in (2, -2)) or (move_distance[0] in (2, -2) and move_distance[1] in (1, -1))


class Bishop(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 3

    def __str__(self):
        if self.color == Color.BLACK:
            return "♗"
        elif self.color == Color.WHITE:
            return "♝"

    def __repr__(self):
        return f"Bishop('{self.color}', '{self.location}')"

    def can_move_to(self, location, game):
        if self.location is None:
            return False
        if not game.board.is_move_clear(self.location, location):
            return False
        move_distance = self.location - location
        return abs(move_distance[0]) == abs(move_distance[1])


class Rook(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 5

    def __str__(self):
        if self.color == Color.BLACK:
            return "♖"
        elif self.color == Color.WHITE:
            return "♜"

    def __repr__(self):
        return f"Rook('{self.color}', '{self.location}')"

    def can_move_to(self, location, game):
        if self.location is None:
            return False
        move_distance = self.location - location
        if move_distance[0] != 0 and move_distance[1] != 0:
            return False
        if not game.board.is_move_clear(self.location, location):
            return False
        return True

    def move_effects(self, start: str | Location, end: Location, game):
        self.has_moved = True


class Queen(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 9

    def __str__(self):
        if self.color == Color.BLACK:
            return "♕"
        elif self.color == Color.WHITE:
            return "♛"

    def __repr__(self):
        return f"Queen('{self.color}', '{self.location}')"

    def can_move_to(self, location, game):
        if self.location is None:
            return False
        move_distance = self.location - location
        if abs(move_distance[0]) != abs(move_distance[1]) and (move_distance[0] != 0 and move_distance[1] != 0):
            return False
        if not game.board.is_move_clear(self.location, location):
            return False
        return True


class King(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 100

    def __str__(self):
        if self.color == Color.BLACK:
            return "♔"
        elif self.color == Color.WHITE:
            return "♚"

    def __repr__(self):
        return f"King('{self.color}', '{self.location}')"

    def move_effects(self, start: str | Location, end: Location, game):
        self.has_moved = True

    def is_in_check(self, board):
        for piece in board.pieces[self.anticolor()]:
            if piece.can_take(self.location, board):
                return True
        return False

    def is_checkmate(self, game):
        for y in (-1, 0, 1):
            for x in (-1, 0, 1):
                if x == 0 and y == 0:  # Skip the square where the king currently is
                    continue
                target_square = f"{chr(ord(self.location[0]) + x)}{(int(self.location[1]) + y)}"
                if not game.board.is_valid_square_name(target_square):
                    continue
                if self.can_move_to(target_square, game):
                    return False
        return True

    def can_move_to(self, location, game):
        move_distance = self.location - location
        if move_distance[0] not in (1, 0, -1) or move_distance[1] not in (1, 0, -1):
            return False
        if location is None:
            raise ValueError("Location cannot be None")

        for piece in game.pieces[self.anticolor()]:
            if piece.can_take(location, game):
                print(f"{piece} can take {location}")
                return False
        return True
