import pytest

from boardng import Board


class TestBoardNg:

    def test_square_to_index(self):
        board = Board()
        assert board.square_to_index['a1'] == 0
        assert board.square_to_index['a2'] == 8
        assert board.square_to_index['b1'] == 1
        assert board.square_to_index['b2'] == 9
        assert board.square_to_index['c1'] == 2

    def test_index_to_square(self):
        board = Board()
        assert board.index_to_square[0] == 'a1'
        assert board.index_to_square[8] == 'a2'
        assert board.index_to_square[1] == 'b1'
        assert board.index_to_square[9] == 'b2'
        assert board.index_to_square[2] == 'c1'

    def test_reset_board(self):
        board = Board()
        board.setup_board()
        assert board.get_piece('a1') == 'R'
        assert board.get_piece('a8') == 'r'
        assert board.get_piece('b1') == 'N'
        assert board.get_piece('b8') == 'n'
        assert board.get_piece('a2') == 'P'
        assert board.get_piece('b7') == 'p'
        assert board.get_piece('e8') == 'k'
        assert board.get_piece('e1') == 'K'

    def test_get_possible_moves(self):
        board = Board()
        board['h8'] = 'r'
        assert board.get_possible_moves('h8') == {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8'}
        board['a1'] = 'r'
        assert board.get_possible_moves('a1') == {'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1'}
        board['a2'] = 'P'
        assert board.get_possible_moves('a2') == {'a3', 'a4'}
        board['a7'] = 'p'
        assert board.get_possible_moves('a7') == {'a5', 'a6'}
        del board['a7']
        board['c1'] = 'B'
        assert board.get_possible_moves('c1') == {'b2', 'a3', 'd2', 'e3', 'f4', 'g5', 'h6'}
        board['b1'] = 'N'
        assert board.get_possible_moves('b1') == {'a3', 'c3', 'd2'}

    def test_get_intermediate_squares(self):
        assert list(Board.get_intermediate_squares('a2', 'a5')) == ['a3', 'a4', 'a5']
        assert list(Board.get_intermediate_squares('a1', 'a8')) == ['a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8']
        assert list(Board.get_intermediate_squares('a1', 'h8')) == ['b2', 'c3', 'd4', 'e5', 'f6', 'g7', 'h8']
        assert list(Board.get_intermediate_squares('a1', 'd4')) == ['b2', 'c3', 'd4']
        assert list(Board.get_intermediate_squares('a1', 'h1')) == ['b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1']

    @pytest.fixture
    def chess_board(self):
        board = Board()
        board.setup_board()
        return board

    def test_pawn_moves(self, chess_board):
        # Testing white pawn basic move
        expected_moves = {'e3', 'e4'}  # Assuming the pawn is at e2
        assert chess_board.get_possible_moves('e2') == expected_moves
        # Add more tests for black pawn, captures, en-passant, etc.

    # Testing Knight Moves
    def test_knight_moves(self, chess_board):
        chess_board.clear()
        chess_board.add_piece('N', 'd4')  # Clear the board and add a knight at d4
        expected_moves = {'b5', 'b3', 'c2', 'e2', 'f3', 'f5', 'e6', 'c6'}
        assert chess_board.get_possible_moves('d4') == expected_moves
        # Test edge and corner cases

    def test_bishop_moves(self, chess_board):
        chess_board.clear()
        chess_board.add_piece('B', 'c1')
        assert chess_board.get_possible_moves('c1') == {'b2', 'a3', 'd2', 'e3', 'f4', 'g5', 'h6'}

    def test_rook_moves(self, chess_board):
        chess_board.clear()
        chess_board.add_piece('R', 'a1')
        assert chess_board.get_possible_moves('a1') == {'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1'}

    def test_queen_moves(self, chess_board):
        chess_board.clear()
        chess_board.add_piece('Q', 'd4')
        assert chess_board.get_possible_moves('d4') == {
            'd1', 'd2', 'd3', 'd5', 'd6', 'd7', 'd8', 'a4', 'b4', 'c4', 'e4', 'f4', 'g4', 'h4',
            'c3', 'b2', 'a1', 'e5', 'f6', 'g7', 'h8', 'c5', 'b6', 'a7', 'e3', 'f2', 'g1'}

    def test_king_moves(self, chess_board):
        chess_board.clear()
        chess_board.add_piece('K', 'e4')
        assert chess_board.get_possible_moves('e4') == {'d3', 'd4', 'd5', 'e3', 'e5', 'f3', 'f4', 'f5'}

    def test_generate_diagonal_moves(self):
        board = Board()
        assert board.generate_diagonal_moves('a1') == {'b2', 'h8', 'e5', 'g7', 'c3', 'd4', 'f6'}
        assert board.generate_diagonal_moves('h1') == {'b7', 'f3', 'a8', 'g2', 'd5', 'c6', 'e4'}
        assert board.generate_diagonal_moves('d4') == {'c3', 'b2', 'a1', 'e5', 'f6', 'g7', 'h8', 'c5', 'b6', 'a7', 'e3', 'f2', 'g1'}

    def test_generate_horiz_vert_moves(self):
        board = Board()
        assert board.generate_horiz_vert_moves('d4') == {'d1', 'd2', 'd3', 'd5', 'd6', 'd7', 'd8', 'a4', 'b4', 'c4', 'e4', 'f4', 'g4', 'h4'}

    def test_compute_all_moves_and_captures(self):
        board = Board()
        board.setup_board()
        x=board.compute_all_moves_and_captures()
        print(1)

