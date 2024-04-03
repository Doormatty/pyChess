import re
import sys

from board import Board
from pieces import Rook, Knight, Bishop, King, Queen, Pawn


class PgnLoader:
    class PgnLoaderException(Exception):
        def __init__(self, message, board, highlights=None):
            super().__init__(message)
            self.board = board
            self.message = message
            self.highlights = highlights

        def __str__(self):
            return f"{super().__str__()}\n{self.board.create_board_text(highlights=self.highlights)}"

    def __init__(self):
        self.data = None
        self.tags = None
        self.moves = None
        self.board = Board()
        self.board.initialize_board()
        self.original = None

    def __getattr__(self, name):
        return self.tags.get(name.lower(), None)

    @property
    def vs_str(self):
        return f"{self.tags['white']} v. {self.tags['black']}"

    def _clear(self):
        self.data = None
        self.tags = None
        self.moves = None
        self.board = Board()
        self.board.initialize_board()

    def load_file(self, filename):
        self._clear()
        with open(filename, 'r') as file:
            self.data = file.read()
            self.extract_tags()
            self.extract_moves()

    def load_str(self, string):
        self._clear()
        self.original = string
        self.data = string
        self.extract_tags()
        self.extract_moves()

    def extract_tags(self):
        pattern = r'\[(\w+) (\".*\")\]'
        tags = {k.lower(): v[1:-1] for k, v in re.findall(pattern, self.data)}
        self.tags = tags

    def extract_moves(self):
        # Removing comments enclosed in {}
        only_moves = '\n'.join([x for x in self.data.split('\n') if not x.startswith('[')])

        pgn_no_comments = re.sub(r'\{.*?\}', '', only_moves)
        moves = re.findall(r'(?:[NBRQK]?[a-h]?\d?\+?x?[a-h]\d\+?|O-O(?:-O)?)[+#]?', pgn_no_comments)
        self.moves = moves

    @staticmethod
    def move_parser(move):
        pattern = r'((?P<source_type>[KQNBR])?(?P<source_square>[a-h][1-8]?)?(?P<capture>x)?(?P<dest_type>[KQNBR])?(?P<dest_square>[a-h][1-8])(?P<check>\+)?)?(?P<kscastle>O-O)?(?P<qscastle>O-O-O)?'
        parts = re.match(pattern, move)
        type_dict = {'K': King, 'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight}
        return {'source_type': type_dict[parts['source_type']] if parts['source_type'] is not None else Pawn,
                'dest_type': type_dict[parts['dest_type']] if parts['dest_type'] is not None else None,
                'source_square': parts['source_square'],
                'dest_square': parts['dest_square'],
                'capture': parts['capture'],
                'check': parts['check'],
                'king_castle': parts['kscastle'],
                'queen_castle': parts['qscastle']}

    def expand_move(self, move):
        possibles = None
        parts = PgnLoader.move_parser(move)
        source_square = parts['source_square']
        if source_square is None:
            possibles = self.board.who_can_move_to(location=parts['dest_square'], piece_filter=parts['source_type'])
        elif len(source_square) == 1:
            if source_square.isalpha():
                if parts['capture']:
                    possibles = self.board.who_can_capture(location=parts['dest_square'], file_filter=source_square, piece_filter=parts['source_type'])
                else:
                    possibles = self.board.who_can_move_to(location=parts['dest_square'], file_filter=source_square, piece_filter=parts['source_type'])
        if possibles is None or len(possibles) == 0:
            raise self.PgnLoaderException(f"No possibilities were found for {move}", board=self.board, highlights=move)
        if len(possibles) > 1:
            raise self.PgnLoaderException(f"Move {move} is not sufficiently described. {len(possibles)} possibilities {possibles} were found", board=self.board, highlights=move)
        source_square = possibles[0].location
        return source_square, parts['dest_square']

    def iter_moves(self):
        for move in self.moves:
            yield move

    def play_game(self):
        played_moves = []
        for move in self.moves:
            played_moves.append(f"{self.board.active_player}: {move}")
            if move in ("O-O", "O-O-O"):
                self.board.castle(self.board.active_player, move)
            else:
                move_info = self.expand_move(move)
                self.board.move(move_info[0], move_info[1])
        if self.tags['result'] == '1/2-1/2' and not self.board.check_for_checkmate():
            pass
            #print("Game ends in Draw")


# Extracting the moves using the updated function


if __name__ == '__main__':
    loader = PgnLoader()
    loader.load_file('game1.pgn')
    loader.play_game()
