import pytest

from board import Board
from gui import ChessSquare
from pieces import Pawn, Knight, Bishop, Rook, Queen, King


def try_movements(start, movements, board):
    """
    Attempts a series of movements for a chess piece.

    :param start: The location of the chess piece to move.
    :param movements: A list of consecutive movements for the piece.
    :param board: The chess board.
    """
    color = board[start].color
    old_location = start
    piece = board[old_location]
    for destination in movements:
        board.active_player = color
        board.move(old_location, destination)
        piece.move_effects(destination)
        # Check if the piece is indeed at the new location
        assert piece.location == destination
        assert board[destination] is piece
        assert board[old_location] is None
        old_location = destination


def make_move(setup_board, source, destination, override=True):
    piece = setup_board[source]
    piece_color = piece.color
    if override:
        setup_board.active_player = piece_color
    setup_board.move(source, destination)
    assert isinstance(setup_board[destination], globals()[piece.__class__.__name__])
    assert setup_board[destination].color == piece_color


class TestChessGame:

    @pytest.fixture
    def setup_board(self):
        board = Board()
        board.initialize_board()
        return board

    # Object Creation Tests
    def test_pawn_initialization(self, setup_board):
        pawn = Pawn("white", "a2", setup_board)
        assert pawn.kind == "pawn" and pawn.color == "white" and pawn.location == "a2" and pawn.points == 1

    # Board Initialization Tests
    def test_board_initialization(self, setup_board):
        assert isinstance(setup_board['a2'], Pawn)
        assert isinstance(setup_board['b1'], Knight)

    # Piece Movement Tests
    def test_white_pawn_movement(self, setup_board):
        pawn = setup_board['a2']
        setup_board.move('a2', 'a4')
        assert pawn.location == 'a4'
        assert setup_board['a4'] is pawn
        assert setup_board['a2'] is None
        with pytest.raises(Board.MoveException):
            setup_board.move('a4', 'a6')
        setup_board.active_player = 'white'
        setup_board.move('a4', 'a5')
        assert pawn.location == 'a5' and setup_board['a5'] is pawn and setup_board['a4'] is None
        pawn = setup_board['b2']
        setup_board.active_player = 'white'
        with pytest.raises(Board.MoveException):
            setup_board.move('b2', 'a6')
            setup_board.move('b2', 'b6')
            setup_board.move('b2', 'u8')
            setup_board.move('b2', 'z2')
            setup_board.move('b2', 'xx')
            setup_board.move('b2', '22')
            setup_board.move('b2', '923')
            setup_board.move('b2', 'abc')
            setup_board.move('b2', "knight to queen's bishop")
        setup_board.active_player = 'white'
        setup_board.move('b2', 'b4')
        assert pawn.location == 'b4' and setup_board['b4'] is pawn and setup_board['b2'] is None
        with pytest.raises(Board.MoveException):
            setup_board.move('b4', 'b3')

    def test_black_pawn_movement(self, setup_board):
        setup_board.active_player = 'black'
        pawn = setup_board['a7']
        setup_board.active_player = 'black'
        setup_board.move('a7', 'a5')
        assert pawn.location == 'a5' and setup_board['a5'] is pawn and setup_board['a7'] is None
        with pytest.raises(Board.MoveException):
            setup_board.move('a5', 'a3')
        setup_board.active_player = 'black'
        setup_board.move('a5', 'a4')
        assert pawn.location == 'a4' and setup_board['a4'] is pawn and setup_board['a5'] is None
        pawn = setup_board['b7']
        setup_board.active_player = 'black'
        with pytest.raises(Board.MoveException):
            setup_board.move('b7', 'a6')
            setup_board.move('b7', 'b1')
            setup_board.move('b7', 'u8')
            setup_board.move('b7', 'z2')
            setup_board.move('b7', 'xx')
            setup_board.move('b7', '22')
            setup_board.move('b7', '923')
            setup_board.move('b7', 'abc')
            setup_board.move('b7', "knight to queen's bishop")
        setup_board.active_player = 'black'
        setup_board.move('b7', 'b5')
        assert pawn.location == 'b5' and setup_board['b5'] is pawn and setup_board['b7'] is None
        with pytest.raises(Board.MoveException):
            setup_board.move('b5', 'b3')

    def test_knight_movement(self, setup_board):
        try_movements('b1', ["c3", "b5", "a3", "b1"], setup_board)

    # Test Bishop Movements
    def test_bishop_movement(self, setup_board):
        setup_board.clear()
        bishop = Bishop("white", "c1", setup_board)
        setup_board['c1'] = bishop
        setup_board.move('c1', 'a3')
        assert bishop.location == "a3" and setup_board["a3"] is bishop
        # Add additional assertions for invalid moves and black bishop

    # Test Rook Movements
    def test_rook_movement(self, setup_board):
        setup_board.clear()
        rook = Rook("white", "a1", setup_board)
        setup_board['a1'] = rook
        setup_board.move('a1', 'a4')
        assert rook.location == "a4" and setup_board["a4"] is rook
        # Add additional assertions for invalid moves and black rook

    # Test Queen Movements
    def test_queen_movement(self, setup_board):
        setup_board.clear()
        queen = Queen("white", "d1", setup_board)
        setup_board['d1'] = queen
        setup_board.move('d1', 'd3')
        assert queen.location == "d3" and setup_board["d3"] is queen
        # Add additional assertions for diagonal, horizontal moves and black queen

    # Test King Movements
    def test_king_movement(self, setup_board):
        setup_board.clear()
        king = King("white", "e1", setup_board)
        setup_board['e1'] = king
        setup_board.move('e1', 'e2')
        assert king.location == "e2" and setup_board["e2"] is king
        # Add additional assertions for invalid moves and black king

    # Boundary and Exception Tests
    def test_out_of_bounds_movement(self, setup_board):
        pawn = setup_board['a2']
        setup_board['a2'] = pawn
        with pytest.raises(Board.MoveException):
            setup_board.move('a2', 'a9')

    # Capture Mechanics Tests
    def test_capture_mechanics(self, setup_board):
        black_pawn = Pawn("black", "b3", setup_board)  # Setup a black pawn
        setup_board['b3'] = black_pawn
        white_pawn = setup_board['a2']
        setup_board.move('a2', 'b3')  # White pawn captures black pawn
        assert white_pawn.location == 'b3' and isinstance(setup_board.captured[0], Pawn) and setup_board.captured[0].color == "black"

    def test_get_intermediate_squares(self):
        assert list(Board.get_intermediate_squares('a2', 'a5')) == ['a3', 'a4']
        assert list(Board.get_intermediate_squares('a1', 'a8')) == ['a2', 'a3', 'a4', 'a5', 'a6', 'a7']
        assert list(Board.get_intermediate_squares('a1', 'h8')) == ['b2', 'c3', 'd4', 'e5', 'f6', 'g7']
        assert list(Board.get_intermediate_squares('a1', 'd4')) == ['b2', 'c3']
        assert list(Board.get_intermediate_squares('a1', 'h1')) == ['b1', 'c1', 'd1', 'e1', 'f1', 'g1']

    def test_extended_capture_mechanics(self, setup_board):
        # Setting up black and white pawns
        setup_board['b3'] = Pawn("black", "b3", setup_board)
        setup_board['c3'] = Pawn("black", "c3", setup_board)
        setup_board['d3'] = Pawn("black", "d3", setup_board)
        setup_board['e3'] = Pawn("black", "e3", setup_board)

        # Setting up other black pieces
        setup_board['c6'] = Knight("black", "c6", setup_board)
        setup_board['f6'] = Bishop("black", "f6", setup_board)

        # White pawn captures black pawn
        make_move(setup_board, 'a2', 'b3')

        # White pawn captures another black pawn
        pawn_b2 = setup_board['b2']
        setup_board.active_player = 'white'
        setup_board.move('b2', 'c3')
        assert pawn_b2.location == 'c3' and isinstance(setup_board.captured[1], Pawn) and setup_board.captured[1].color == "black"

        # White knight capturing black pawn
        setup_board['d5'] = Knight("white", "d5", setup_board)
        knight_d5 = setup_board['d5']
        setup_board.active_player = 'white'
        setup_board.move('d5', 'e3')
        assert knight_d5.location == 'e3' and isinstance(setup_board.captured[2], Pawn) and setup_board.captured[2].color == "black"

    def test_game_simulation_with_captures(self, setup_board):
        # Move white pawn from e2 to e4
        make_move(setup_board, 'e2', 'e4')
        # Move black pawn from d7 to d5
        make_move(setup_board, 'd7', 'd5')
        # White pawn captures black pawn
        make_move(setup_board, 'e4', 'd5')
        # Move black knight from b8 to c6
        make_move(setup_board, 'b8', 'c6')
        # Move white bishop from f1 to c4
        make_move(setup_board, 'f1', 'c4')
        # Move black pawn from e7 to e6
        make_move(setup_board, 'e7', 'e6')
        # Move white knight from g1 to f3
        make_move(setup_board, 'g1', 'f3')
        # Move black bishop from c8 to g4
        make_move(setup_board, 'c8', 'g4')
        # White knight from b1 to c3
        make_move(setup_board, 'b1', 'c3')
        # Black queen moves from d8 to h4
        make_move(setup_board, 'd8', 'h4')
        # White bishop captures black pawn
        make_move(setup_board, 'c4', 'e6')

    @pytest.mark.parametrize("square,expected_index", [
        ('a1', 0),
        ('h8', 63),
        ('e4', 28),
        ('c6', 42),
    ])
    def test_square_to_index(self, square, expected_index):
        assert ChessSquare.square_to_index(square) == expected_index

