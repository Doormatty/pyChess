class Piece:
    class MoveException(Exception):
        pass

    def __init__(self, color, location):
        self._location = location
        if location is not None:
            self.int_vert = int(self._location[1])
            self.int_horz = ord(self._location[0].lower())
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
            self._location = value
            self.int_vert = int(self._location[1])
            self.int_horz = ord(self._location[0].lower())

    def anticolor(self):
        if self.color == "black":
            return "white"
        else:
            return "black"

    def can_move_to(self, location: str, board):
        raise NotImplementedError

    def can_take(self, location: str, board) -> bool:
        return self.can_move_to(location, board) and board[location] is not None and board[location].color == self.anticolor()

    def get_all_possible_moves(self, board) -> list[str]:
        possible_moves = []
        for square in board.iter_square_names():
            if self.can_move_to(square, board) or self.can_take(square, board):
                possible_moves.append(square)
        return possible_moves

    def move_effects(self, location, board):
        board.enpassants = []


class Pawn(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 1

    def __str__(self):
        if self.color == "black":
            return "♙"
        elif self.color == "white":
            return "♟"

    def __repr__(self):
        return f"Pawn('{self.color}', '{self.location}')"

    def _enpassant_squares(self) -> tuple[str] | tuple[str, str] | list:
        if self.has_moved:
            return []
        h = self.location[0]
        v = int(self.location[1])
        if self.color == "black":
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

    def move_effects(self, location: str, board):
        if self.location is None:
            return
        board.halfmove_counter = 0
        possible_enpassants = []
        # for square in self._enpassant_squares():
        #     if board[square] is not None and board[square].__class__.__name__ == "Pawn" and board[square].color == self.anticolor():
        #         possible_enpassants.append(square)
        # if possible_enpassants:
        #     board.enpassants = possible_enpassants
        if self.color == 'black':
            board.enpassants = [f"{self.location[0]}{self.int_vert + 1}"]
        else:
            board.enpassants = [f"{self.location[0]}{self.int_vert - 1}"]
        self.has_moved = True

    def can_move_to(self, location: str, board):
        if self.location is None:
            return False
        move_distance = board.get_move_distance(self.location, location)
        if move_distance[0] != 0:
            return False
        if not board.is_move_clear(self.location, location):
            return False
        color = 1 if self.color == "white" else -1
        if move_distance[1] == (1 * color):
            return True
        if move_distance[1] == (2 * color) and not self.has_moved:
            return True
        return False

    def can_take(self, location: str, board):
        if self.location is None:
            raise self.MoveException("Can't move a piece that doesn't have a location")
        move_distance = board.get_move_distance(self.location, location)
        if move_distance[0] in (1, -1) and ((move_distance[1] == 1 and self.color == "white") or (move_distance[1] == -1 and self.color == "black")):
            return True
        if location in board.enpassants and board[location].__class__.__name__ == "Pawn":
            return True
        return False


class Knight(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 3

    def __str__(self):
        if self.color == "black":
            return "♘"
        elif self.color == "white":
            return "♞"

    def __repr__(self):
        return f"Knight('{self.color}', '{self.location}')"

    def can_move_to(self, location, board):
        if self.location is None:
            return False
        move_distance = board.get_move_distance(self.location, location)
        return (move_distance[0] in (1, -1) and move_distance[1] in (2, -2)) or (move_distance[0] in (2, -2) and move_distance[1] in (1, -1))


class Bishop(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 3

    def __str__(self):
        if self.color == "black":
            return "♗"
        elif self.color == "white":
            return "♝"

    def __repr__(self):
        return f"Bishop('{self.color}', '{self.location}')"

    def can_move_to(self, location, board):
        if self.location is None:
            return False
        if not board.is_move_clear(self.location, location):
            return False
        move_distance = board.get_move_distance(self.location, location)
        return abs(move_distance[0]) == abs(move_distance[1])


class Rook(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 5

    def __str__(self):
        if self.color == "black":
            return "♖"
        elif self.color == "white":
            return "♜"

    def __repr__(self):
        return f"Rook('{self.color}', '{self.location}')"

    def can_move_to(self, location, board):
        if self.location is None:
            return False
        if not board.is_move_clear(self.location, location):
            return False
        move_distance = board.get_move_distance(self.location, location)
        return move_distance[0] == 0 or move_distance[1] == 0

    def move_effects(self, location: str, board):
        self.has_moved = True


class Queen(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 9

    def __str__(self):
        if self.color == "black":
            return "♕"
        elif self.color == "white":
            return "♛"

    def __repr__(self):
        return f"Queen('{self.color}', '{self.location}')"

    def can_move_to(self, location, board):
        if self.location is None:
            return False
        if not board.is_move_clear(self.location, location):
            return False
        move_distance = board.get_move_distance(self.location, location)
        return abs(move_distance[0]) == abs(move_distance[1]) or (move_distance[0] == 0 or move_distance[1] == 0)


class King(Piece):
    def __init__(self, color, location):
        super().__init__(color=color, location=location)
        self.points = 100

    def __str__(self):
        if self.color == "black":
            return "♔"
        elif self.color == "white":
            return "♚"

    def __repr__(self):
        return f"King('{self.color}', '{self.location}')"

    def move_effects(self, location: str, board):
        self.has_moved = True

    def is_checkmate(self, board):
        all_adjacent_squares_blocked = True
        for y in (-1, 0, 1):
            for x in (-1, 0, 1):
                if x == 0 and y == 0:  # Skip the square where the king currently is
                    continue
                target_square = f"{chr(ord(self.location[0]) + x)}{(int(self.location[1]) + y)}"
                if not board._boundry_check(target_square):
                    continue
                if self.can_move_to(target_square, board):
                    return False
                elif board[target_square] is None or board[target_square].color != self.color:
                    all_adjacent_squares_blocked = False
        return all_adjacent_squares_blocked

    def can_move_to(self, location, board):
        move_distance = board.get_move_distance(self.location, location)
        if move_distance[0] not in (1, 0, -1) or move_distance[1] not in (1, 0, -1):
            return False
        if location is None:
            raise ValueError("Location cannot be None")
        for piece in board.pieces[self.anticolor()]:
            if isinstance(piece, King):
                continue
            if piece.can_take(location, board):
                return False
        return True
