class Piece:
    class MoveException(Exception):
        pass

    def __init__(self, color, kind, location, board):
        if isinstance(location, int):
            self.location = self.index_to_square(location)
        else:
            self.location = location

        self.kind = kind
        self.color = color
        self.board = board
        self.points = None
        self.has_moved = False

    @staticmethod
    def iter_square_names():
        for letter in "abcdefgh":
            for number in range(1, 9):
                yield f'{letter}{number}'

    @staticmethod
    def get_move_distance(source, destination):
        vertical = int(destination[1]) - int(source[1])
        horizontal = abs(ord(destination[0].lower()) - ord(source[0].lower()))
        return horizontal, vertical

    @staticmethod
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
        return self.can_move_to(location)

    def get_all_possible_moves(self):
        possible_moves = []
        for square in self.iter_square_names():
            if self.can_move_to(square):
                possible_moves.append(square)
        return possible_moves

    def move_effects(self, location):
        pass


class Pawn(Piece):
    def __init__(self, color, location, board):
        if isinstance(location, int):
            location = self.index_to_square(location)
        super().__init__(kind="pawn", color=color, location=location, board=board)
        self.points = 1
        self.starting_position = None
        if location[1] in ('2', '7'):
            self.starting_position = True

    def __str__(self):
        if self.color == "black":
            return "♙"
        elif self.color == "white":
            return "♟"

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
            if self.board[square] is not None and self.board[square].kind == "pawn" and self.board[square].color == self.anticolor():
                possible_enpassants.append(square)
        if possible_enpassants:
            self.board.enpassants[self.color] = possible_enpassants

    def can_move_to(self, location):
        move_distance = self.get_move_distance(self.location, location)

        if self.color == "white":
            if move_distance[0] == 0:
                if move_distance[1] == 1:  # Move one square forward
                    return True
                if move_distance[1] == 2 and self.starting_position:  # Move two squares from starting position
                    return True

        elif self.color == "black":
            if move_distance[0] == 0:
                if move_distance[1] == -1:
                    return True
                if move_distance[1] == -2 and self.starting_position:
                    return True

        return False

    def can_take(self, location):
        move_distance = self.get_move_distance(self.location, location)
        if move_distance[0] == 1 and (move_distance[1] == 1 or (move_distance[1] == -1 and self.color == "black")):
            return True
        else:
            return False


class Knight(Piece):
    def __init__(self, color, location, board):
        super().__init__(kind="knight", color=color, location=location, board=board)
        self.points = 3

    def __str__(self):
        if self.color == "black":
            return "♘"
        elif self.color == "white":
            return "♞"

    def can_move_to(self, location):
        move_distance = self.get_move_distance(self.location, location)
        return (abs(move_distance[0]) == 1 and abs(move_distance[1]) == 2) or (abs(move_distance[0]) == 2 and abs(move_distance[1]) == 1)


class Bishop(Piece):
    def __init__(self, color, location, board):
        super().__init__(kind="bishop", color=color, location=location, board=board)
        self.points = 3

    def __str__(self):
        if self.color == "black":
            return "♗"
        elif self.color == "white":
            return "♝"

    def can_move_to(self, location):
        move_distance = self.get_move_distance(self.location, location)
        return abs(move_distance[0]) == abs(move_distance[1])


class Rook(Piece):
    def __init__(self, color, location, board):
        super().__init__(kind="rook", color=color, location=location, board=board)
        self.points = 5

    def __str__(self):
        if self.color == "black":
            return "♖"
        elif self.color == "white":
            return "♜"

    def can_move_to(self, location):
        move_distance = self.get_move_distance(self.location, location)
        return abs(move_distance[0]) == 0 or abs(move_distance[1]) == 0


class Queen(Piece):
    def __init__(self, color, location, board):
        super().__init__(kind="queen", color=color, location=location, board=board)
        self.points = 9

    def __str__(self):
        if self.color == "black":
            return "♕"
        elif self.color == "white":
            return "♛"

    def can_move_to(self, location):
        move_distance = self.get_move_distance(self.location, location)
        return abs(move_distance[0]) == abs(move_distance[1]) or (abs(move_distance[0]) == 0 or abs(move_distance[1]) == 0)


class King(Piece):
    def __init__(self, color, location, board):
        super().__init__(kind="king", color=color, location=location, board=board)
        self.points = 100

    def __str__(self):
        if self.color == "black":
            return "♔"
        elif self.color == "white":
            return "♚"

    def can_move_to(self, location):
        move_distance = self.get_move_distance(self.location, location)
        if abs(move_distance[0]) <= 1 and abs(move_distance[1]) <= 1:
            return True
        return False
