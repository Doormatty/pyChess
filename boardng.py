from functools import cache


class Board:
    index_to_square = {rank * 8 + file: f"{chr(file + 97)}{rank + 1}" for rank in range(8) for file in range(8)}
    square_to_index = {f"{chr(file + 97)}{rank + 1}": rank * 8 + file for rank in range(8) for file in range(8)}

    class BoardException(Exception):
        pass

    def __init__(self):
        self._initialize_board()

    def __setitem__(self, value, square):
        self.add_piece(square, value)

    def __delitem__(self, square):
        self.board[Board.square_to_index[square]] = None

    def clear(self):
        self._initialize_board()

    def _initialize_board(self):
        self.board: list[None | str] = [None] * 64
        self.black_king_moved = False
        self.white_king_moved = False
        self.black_kingside_rook_moved = False
        self.white_kingside_rook_moved = False
        self.black_queenside_rook_moved = False
        self.white_queenside_rook_moved = False

    def setup_board(self):
        self.board = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'] + ['P'] * 8 + [None] * 32 + ['p'] * 8 + ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']

    def add_piece(self, piece, square):
        index = Board.square_to_index[square]
        if self.board[index] is not None:
            raise Board.BoardException(f"Can't add {piece} to square {square}, already occupied by {self.board[index]}")
        self.board[index] = piece

    def move_piece(self, start_square, end_square):
        start_index = Board.square_to_index[start_square]
        end_index = Board.square_to_index[end_square]
        start_piece = self.board[start_index]
        end_piece = self.board[end_index]
        self.board[end_index] = start_piece
        self.board[start_index] = None
        if end_piece is not None:
            return end_piece

    def get_piece(self, square):
        return self.board[Board.square_to_index[square]]

    def get_possible_moves(self, square) -> set[str] | None:
        piece = self.get_piece(square)
        if piece is None:
            return None
        if piece in 'pP':
            moves = self.get_possible_pawn_moves(square)
        elif piece in 'rR':
            moves = self.get_possible_rook_moves(square)
        elif piece in 'nN':
            moves = self.get_possible_knight_moves(square)
        elif piece in 'bB':
            moves = self.get_possible_bishops_moves(square)
        elif piece in 'kK':
            moves = self.get_possible_king_moves(square)
            print(1)
        elif piece in 'qQ':
            moves = self.get_possible_queen_moves(square)
        else:
            return None
        if moves is not None:
            moves.discard(square)
            clear_moves = self.get_clear_moves(square, moves)
            if clear_moves:
                return clear_moves

    def get_clear_moves(self, start: str, moves: set) -> set[str]:
        clear_moves = {move for move in moves if self.is_move_clear(start, move)}
        return clear_moves

    @staticmethod
    def are_same_color(piece1: str, piece2: str) -> bool:
        """
        Check if two pieces are of the same color based on their case.
        Both pieces should be non-empty strings representing chess pieces:
        'KQRBNP' for white; 'kqrbnp' for black.

        Args:
        piece1 (str): The character representing the first piece.
        piece2 (str): The character representing the second piece.

        Returns:
        bool: True if both pieces are the same color, False otherwise.
        """
        if piece1.isalpha() and piece2.isalpha():
            return piece1.isupper() == piece2.isupper()
        return False  # Return False if either input is not a valid piece representation

    def can_capture(self, square, target_square):
        piece = self.get_piece(square)
        target_piece = self.get_piece(target_square)
        if piece is None:
            raise Board.BoardException(f"None can't capture anything.")
        if target_piece is None:
            raise Board.BoardException(f"Can't capture a None.")
        if self.are_same_color(piece, target_piece):
            return False
        if piece in 'Pp':
            color = -1 if piece.islower() else 1
            if ord(target_square[0]) in (ord(square[0]) + 1, ord(square[0]) - 1) and (square[1] + color == target_square[1]):
                return True
        elif self.get_piece(square) in 'Kk':
            pass
        else:
            return target_square in self.get_possible_moves(square)

    @staticmethod
    @cache
    def generate_diagonal_moves(square):
        diagonals = set()
        # Check each diagonal direction [top-right, bottom-right, bottom-left, top-left]
        for dx, dy in [(1, 1), (1, -1), (-1, -1), (-1, 1)]:
            tx = ord(square[0]) - 97
            ty = int(square[1]) - 1
            while 0 <= tx + dx < 8 and 0 <= ty + dy < 8:
                tx += dx
                ty += dy
                diagonals.add(chr(tx + 97) + str(ty + 1))
        return diagonals

    @staticmethod
    @cache
    def generate_horiz_vert_moves(square):
        moves = set()
        for r in '12345678':
            moves.add(f"{square[0]}{r}")
            moves.add(f"{chr(int(r) + 96)}{square[1]}")
        return moves - {square}

    @staticmethod
    def get_possible_queen_moves(square):
        return Board.generate_horiz_vert_moves(square) | Board.generate_diagonal_moves(square)

    @staticmethod
    def get_possible_rook_moves(square):
        return Board.generate_horiz_vert_moves(square)

    @staticmethod
    def get_possible_bishops_moves(square):
        return Board.generate_diagonal_moves(square)

    @staticmethod
    def _generate_moves_from_movelist(square, movelist):
        moves = []
        file = ord(square[0]) - 96
        rank = int(square[1])

        for move in movelist:
            new_file = file + move[0]
            new_rank = rank + move[1]
            if 1 <= new_file <= 8 and 1 <= new_rank <= 8:
                moves.append(f"{chr(new_file + 96)}{str(new_rank)}")
        return set(moves)

    @staticmethod
    @cache
    def get_possible_knight_moves(square):
        return Board._generate_moves_from_movelist(square, [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)])

    def get_possible_pawn_moves(self, square):
        moves = []
        color = -1 if self.get_piece(square).islower() else 1
        moves.append(square[0] + str(int(square[1]) + color))
        if (square[1] == '2' and color == 1) or (square[1] == '7' and color == -1):
            moves.append(square[0] + str(int(square[1]) + color * 2))
        return set(moves)

    @staticmethod
    @cache
    def get_possible_king_moves(square):
        return Board._generate_moves_from_movelist(square, [(0, -1), (0, 1), (1, 0), (-1, 0), (1, -1), (1, 1), (-1, -1), (-1, 1)])

    @staticmethod
    @cache
    def get_move_distance(start: str, end: str) -> tuple[int, int]:
        return ord(end[0]) - ord(start[0]), int(end[1]) - int(start[1])

    @staticmethod
    @cache
    def get_intermediate_squares(start: str, end: str) -> list[str]:
        """
        Get all squares that a piece must cross to get from start to end.
        This does not include the start square but includes the end square.

        Parameters:
        start (str): The starting square in chess notation, for example, 'd5'.
        end (str): The ending square in chess notation, for example, 'e7'.

        Yields:
        str: The squares in the path from start to end.
        """
        start_file = ord(start[0])
        start_rank = int(start[1])
        end_file = ord(end[0])
        end_rank = int(end[1])

        move_distance = (end_file - start_file, end_rank - start_rank)
        moves = []

        if abs(move_distance[0]) == abs(move_distance[1]):
            # Diagonal move
            step_x = 1 if start_file < end_file else -1
            step_y = 1 if start_rank < end_rank else -1
            for i in range(1, abs(move_distance[0])):
                moves.append(f'{chr(start_file + i * step_x)}{start_rank + i * step_y}')

        elif abs(move_distance[0]) == 0:
            # Vertical move e.g. B6 -> B2 - change in Rank
            step = 1 if start_rank < end_rank else -1
            for rank in range(start_rank + step, end_rank, step):
                moves.append(f'{chr(start_file)}{rank}')

        elif abs(move_distance[1]) == 0:
            # Horizontal move e.g. D2 -> H2 - change in File
            step = 1 if start_file < end_file else -1
            for file in range(start_file + step, end_file, step):
                moves.append(f'{chr(file)}{end_rank}')
        moves.append(end)
        return moves

    def is_move_clear(self, start_square, end_square):
        if self.get_piece(start_square) in 'Nn':
            return True
        inter_squares = list(self.get_intermediate_squares(start_square, end_square))
        for square in inter_squares:
            if self.get_piece(square) is not None:
                return False
        return True

    def compute_all_moves_and_captures(self):
        all_moves = {}
        for i, piece in enumerate(self.board):
            if piece:
                position = self.index_to_square[i]
                result = self.get_possible_moves_and_captures(position)
                if result:
                    all_moves[position] = {'moves': result[0], 'captures': result[1]}
        return all_moves

    def get_possible_moves_and_captures(self, square):
        possible_moves = self.get_possible_moves(square)
        moves = set()
        captures = set()
        if not possible_moves:
            return None
        for move in possible_moves:
            if self.get_piece(move) and self.can_capture(square, move):
                captures.add(move)
            else:
                moves.add(move)

        return moves, captures if captures else None

    def print(self):
        print('   abcdefgh  ')
        for i in range(8):
            print(8 - i, '|', end='')
            print(''.join([_ if _ is not None else ' ' for _ in self.board[i * 8: (i + 1) * 8]]), end='')
            print(f'|{8 - i}')
        print('   abcdefgh  ')


if __name__ == '__main__':
    board = Board()
    board.setup_board()
    board.print()
    x = board.compute_all_moves_and_captures()
    print(1)
