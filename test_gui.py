from gui import ChessSquare


class TestGUI:

    def test_square_to_index(self):
        assert ChessSquare.square_to_index('a1') == 0
        assert ChessSquare.square_to_index('h1') == 7
        assert ChessSquare.square_to_index('a8') == 56
        assert ChessSquare.square_to_index('h8') == 63

    def test_index_to_square(self):
        assert ChessSquare.index_to_square(0) == 'a1'
        assert ChessSquare.index_to_square(7) == 'h1'
        assert ChessSquare.index_to_square(56) == 'a8'
        assert ChessSquare.index_to_square(63) == 'h8'

