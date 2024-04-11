from copy import deepcopy

import pytest

from board import Board
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
    setup_board.move(source, destination, override=override)
    assert isinstance(setup_board[destination], globals()[piece.__class__.__name__])
    assert setup_board[destination].color == piece_color


class TestChessGame:
    # Edge Case Tests
    def test_pawn_promotion(self, setup_board):
        # Move white pawn to the last rank
        setup_board.active_player = 'white'
        setup_board.move('a2', 'a7')
        setup_board.move('a7', 'a8')
        # Ensure pawn is promoted to a queen by default
        assert isinstance(setup_board['a8'], Queen)
        assert setup_board['a8'].color == 'white'

    def test_en_passant_capture(self, setup_board):
        # Simulate the conditions for en passant
        setup_board.active_player = 'white'
        setup_board.move('e2', 'e5')
        setup_board.active_player = 'black'
        setup_board.move('d7', 'd5')
        # Perform en passant capture
        setup_board.active_player = 'white'
        setup_board.move('e5', 'd6')
        assert setup_board['d6'] == Pawn('white', 'd6')
        assert setup_board['d5'] is None
        assert isinstance(setup_board.captured_pieces['black'][-1], Pawn)

    def test_castling(self, setup_board):
        # Clear the path for castling
        setup_board['f1'] = None
        setup_board['g1'] = None
        # Perform kingside castling
        setup_board.active_player = 'white'
        setup_board.move('e1', 'g1')
        assert isinstance(setup_board['g1'], King)
        assert isinstance(setup_board['f1'], Rook)
        # Perform queenside castling
        setup_board['d1'] = None
        setup_board['c1'] = None
        setup_board['b1'] = None
        setup_board.active_player = 'white'
        setup_board.move('e1', 'c1')
        assert isinstance(setup_board['c1'], King)
        assert isinstance(setup_board['d1'], Rook)

    def test_checkmate_detection(self, setup_board):
        # Setup a simple checkmate position
        setup_board.clear()
        setup_board.add_piece(King("black", "a8"))
        setup_board.add_piece(Queen("white", "b6"))
        setup_board.add_piece(King("white", "c6"))
        setup_board.active_player = 'black'
        with pytest.raises(Board.MoveException) as excinfo:
            setup_board.move('a8', 'a7')  # Black king is in checkmate
        assert 'checkmate' in str(excinfo.value).lower()

    def test_stalemate_detection(self, setup_board):
        # Setup a simple stalemate position
        setup_board.clear()
        setup_board.add_piece(King("black", "a8"))
        setup_board.add_piece(Queen("white", "c7"))
        setup_board.add_piece(King("white", "c6"))
        setup_board.active_player = 'black'
        with pytest.raises(Board.MoveException) as excinfo:
            setup_board.move('a8', 'a7')  # Black king has no legal moves but is not in check
        assert 'stalemate' in str(excinfo.value).lower()

    def test_threefold_repetition(self, setup_board):
        # Repeat the same position three times
        setup_board.active_player = 'white'
        setup_board.move('b1', 'c3')
        setup_board.active_player = 'black'
        setup_board.move('b8', 'c6')
        setup_board.active_player = 'white'
        setup_board.move('c3', 'b1')
        setup_board.active_player = 'black'
        setup_board.move('c6', 'b8')
        setup_board.active_player = 'white'
        setup_board.move('b1', 'c3')
        setup_board.active_player = 'black'
        setup_board.move('b8', 'c6')
        setup_board.active_player = 'white'
        setup_board.move('c3', 'b1')
        setup_board.active_player = 'black'
        setup_board.move('c6', 'b8')
        # The position has been repeated three times
        assert setup_board.is_threefold_repetition()

    def test_fifty_move_rule(self, setup_board):
        # Make 50 moves without any pawn movement or capture
        for _ in range(25):
            setup_board.active_player = 'white'
            setup_board.move('b1', 'c3')
            setup_board.active_player = 'black'
            setup_board.move('b8', 'c6')
            setup_board.active_player = 'white'
            setup_board.move('c3', 'b1')
            setup_board.active_player = 'black'
            setup_board.move('c6', 'b8')
        # The 50-move rule should now be in effect
        assert setup_board.is_fifty_move_rule()

    @pytest.fixture
    def setup_board(self):
        board = Board()
        board.initialize_board()
        return board

    # Object Creation Tests
    def test_pawn_initialization(self, setup_board):
        pawn = Pawn("white", "a2")
        assert isinstance(pawn, Pawn) and pawn.color == "white" and pawn.location == "a2" and pawn.points == 1

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
        bishop = Bishop("white", "c1")
        setup_board['c1'] = bishop
        setup_board.move('c1', 'a3')
        assert bishop.location == "a3" and setup_board["a3"] is bishop
        # Add additional assertions for invalid moves and black bishop

    # Test Rook Movements
    def test_rook_movement(self, setup_board):
        setup_board.clear()
        rook = Rook("white", "a1")
        setup_board['a1'] = rook
        setup_board.move('a1', 'a4')
        assert rook.location == "a4" and setup_board["a4"] is rook
        # Add additional assertions for invalid moves and black rook

    # Test Queen Movements
    def test_queen_movement(self, setup_board):
        setup_board.clear()
        queen = Queen("white", "d1")
        setup_board['d1'] = queen
        setup_board.move('d1', 'd3')
        assert queen.location == "d3" and setup_board["d3"] is queen
        # Add additional assertions for diagonal, horizontal moves and black queen

    # Test King Movements
    def test_king_movement(self, setup_board):
        setup_board.clear()
        king = King("white", "e1")
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
    def test_basic_capture_mechanics(self, setup_board):
        setup_board.add_piece(piece=Pawn("black", location="b3"))  # Setup a black pawn
        white_pawn = setup_board['a2']
        setup_board.move('a2', 'b3')  # White pawn captures black pawn
        assert white_pawn.location == 'b3', "The white pawn's location has not been updated"
        assert isinstance(setup_board.captured_pieces['black'][0], Pawn)
        assert setup_board.captured_pieces['black'][0].color == "black"

    def test_get_intermediate_squares(self):
        assert list(Board.get_intermediate_squares('a2', 'a5')) == ['a3', 'a4']
        assert list(Board.get_intermediate_squares('a1', 'a8')) == ['a2', 'a3', 'a4', 'a5', 'a6', 'a7']
        assert list(Board.get_intermediate_squares('a1', 'h8')) == ['b2', 'c3', 'd4', 'e5', 'f6', 'g7']
        assert list(Board.get_intermediate_squares('a1', 'd4')) == ['b2', 'c3']
        assert list(Board.get_intermediate_squares('a1', 'h1')) == ['b1', 'c1', 'd1', 'e1', 'f1', 'g1']

    def test_extended_capture_mechanics(self, setup_board):
        # Setting up black and white pawns
        setup_board.add_piece(Pawn("black", "b3"))
        setup_board.add_piece(Pawn("black", "c3"))
        setup_board.add_piece(Pawn("black", "d3"))
        setup_board.add_piece(Pawn("black", "e3"))

        # Setting up other black pieces
        setup_board.add_piece(Knight("black", "c6"))
        setup_board.add_piece(Bishop("black", "f6"))

        # White pawn captures black pawn
        white_pawn = setup_board['a2']
        setup_board.move('a2', 'b3')
        assert white_pawn.location == 'b3' and isinstance(setup_board.captured_pieces['black'][0], Pawn) and setup_board.captured_pieces['black'][0].color == "black"

        setup_board.move('h7', 'h6')

        # White pawn captures another black pawn
        pawn_b2 = setup_board['b2']
        setup_board.active_player = 'white'
        setup_board.move('b2', 'c3')
        assert pawn_b2.location == 'c3' and isinstance(setup_board.captured_pieces['black'][1], Pawn) and setup_board.captured_pieces['black'][1].color == "black"

        # White knight capturing black pawn
        setup_board.add_piece(Knight("white", "d5"))
        knight_d5 = setup_board['d5']
        setup_board.active_player = 'white'
        setup_board.move('d5', 'e3')
        assert knight_d5.location == 'e3' and isinstance(setup_board.captured_pieces['black'][2], Pawn) and setup_board.captured_pieces['black'][2].color == "black"

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

    def test_tempmove(self):
        board = Board()
        board.initialize_board()
        original_board = deepcopy(board)
        with Board.TempMove(board):
            board.move("b2", "b4")
            assert board['b4'] == Pawn('white', 'b4')
            assert board['b2'] is None

            board.move("e7", "e5")
            assert board['e5'] == Pawn('black', 'e5')
            assert board['e7'] is None

            board.move("g1", "f3")
            assert board['f3'] == Knight('white', 'f3')
            assert board['g1'] is None

            # Bishop takes Pawn
            board.move("f8", "b4")
            assert board['b4'] == Bishop('black', 'b4')
            assert board['f8'] is None

            assert board.captured_pieces == {'white': [Pawn('white', None)], 'black': []}
            assert len(board.pieces['white']) == 15

        assert board['b2'] == Pawn('white', 'b2')
        assert board['b4'] is None
        assert board.captured_pieces == {'white': [], 'black': []}
        assert len(board.pieces['white']) == 16
