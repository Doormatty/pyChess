import re

from board import Board


class PgnLoader:
    class PgnLoaderException(Exception):
        def __init__(self, message, board, highlights=None):
            super().__init__(message)
            self.board = board
            self.message = message
            self.highlights = highlights

        def __str__(self):
            return f"{super().__str__()}\n{self.board.create_board_text(highlight=self.highlights)}"

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

    def iter_moves(self):
        for move in self.moves:
            yield move

    def play_game(self):
        played_moves = []
        for move in self.moves:
            self.board.compact_move(move)


        if self.tags['result'] == '1/2-1/2' and not self.board.check_for_checkmate():
            pass
            # print("Game ends in Draw")


# Extracting the moves using the updated function


if __name__ == '__main__':
    loader = PgnLoader()
    loader.load_file('game1.pgn')
    loader.play_game()
