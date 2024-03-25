from rich import print
from rich.console import Console

from pieces import Pawn, Knight, Bishop, Rook, Queen, King, Piece

console = Console()


class Engine:

    def __init__(self):
        self.active_player = 'white'
        self.turn_number = 0
        self.halfmove_counter = 0
        self.console = Console(width=20)
        self.captured = []
        self.enpassant = dict()
        self.squares = {}
        self.reset()

    def add(self, square, piece):
        self.squares[square].add_piece(piece)

    def move(self, source, dest):
        if self[source] is None:
            raise Piece.MoveException(f"No piece at source square {source}")
        if self[source].color != self.active_player:
            raise Piece.MoveException(f"It's {self.active_player}'s move.")
        self[source].move_effects(dest)
        self._end_turn()

    def _end_turn(self):
        if self.active_player == "black":
            self.turn_number += 1
            self.active_player = "white"
        else:
            self.active_player = "black"

    @staticmethod
    def get_move_distance(source, destination):
        vertical = int(destination[1]) - int(source[1])
        horizontal = abs(ord(destination[0].lower()) - ord(source[0].lower()))
        return horizontal, vertical







