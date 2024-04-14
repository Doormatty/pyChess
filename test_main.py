from copy import deepcopy

import pytest

from board import Board, Color
from game import Game
from pieces import Pawn, Knight, Bishop, Rook, Queen, King
from utils import Location


def try_movements(start, movements, game):
    """
    Attempts a series of movements for a chess piece.

    :param start: The location of the chess piece to move.
    :param movements: A list of consecutive movements for the piece.
    :param game: The chess board.
    """
    color = game.board[start].color
    old_location = start
    piece = game.board[old_location]
    for destination in movements:
        game.active_player = color
        game.move(old_location, destination)
        # Check if the piece is indeed at the new location
        assert piece.location == destination
        assert game.board[destination] is piece
        assert game.board[old_location] is None
        old_location = destination


def make_move(game: Game, source, destination, override=False):
    piece = game.board[source]
    piece_color = piece.color
    if override:
        game.active_player = piece_color
    game.move(source, destination)
    assert isinstance(game.board[destination], globals()[piece.__class__.__name__])
    assert game.board[destination].color == piece_color


class TestChessGame:

    @pytest.fixture
    def setup_game(self):
        game = Game()
        game.reset()
        game.setup_board()
        return game

    # Edge Case Tests
    def test_pawn_promotion(self, setup_game):
        # Move white pawn to the last rank
        setup_game.reset()
        setup_game.add_piece(Pawn(Color.WHITE, "a7"))
        setup_game.active_player = Color.WHITE
        setup_game.move('a7', 'a8')
        setup_game.promote_pawn('a8', 'Queen')
        # Ensure pawn is promoted to a queen by default
        assert isinstance(setup_game.board['a8'], Queen)
        assert setup_game.board['a8'].color == Color.WHITE

    def test_en_passant_capture(self, setup_game):
        # Simulate the conditions for en passant
        setup_game.reset()
        setup_game.add_piece(Pawn(Color.WHITE, "e5"))
        setup_game.add_piece(Pawn(Color.BLACK, "d7"))
        setup_game.active_player = Color.BLACK
        setup_game.move('d7', 'd5')
        # Perform en passant capture
        setup_game.active_player = Color.WHITE
        setup_game.move('e5', 'd6')
        assert setup_game.board['d6'] == Pawn(Color.WHITE, 'd6')
        assert setup_game.board['d5'] is None
        assert isinstance(setup_game.captured_pieces[Color.BLACK][-1], Pawn)

    def test_castling(self, setup_game):
        # Clear the path for castling
        setup_game.board['f1'] = None
        setup_game.board['g1'] = None
        # Perform kingside castling
        setup_game.active_player = Color.WHITE
        setup_game.move('O-O', None)
        assert isinstance(setup_game.board['g1'], King)
        assert isinstance(setup_game.board['f1'], Rook)
        setup_game.setup_board()
        # Perform queenside castling
        setup_game.board['d1'] = None
        setup_game.board['c1'] = None
        setup_game.board['b1'] = None
        setup_game.active_player = Color.WHITE
        setup_game.move('O-O-O', None)
        assert isinstance(setup_game.board['c1'], King)
        assert isinstance(setup_game.board['e1'], Rook)

    def test_checkmate_detection(self, setup_game):
        # Setup a simple checkmate position
        setup_game.reset()
        setup_game.add_piece(King(Color.BLACK, "a8"))
        setup_game.add_piece(Queen(Color.WHITE, "b6"))
        setup_game.add_piece(King(Color.WHITE, "c6"))
        setup_game.active_player = Color.WHITE
        assert setup_game.check_for_checkmate() is True

    # def test_stalemate_detection(self, setup_game):
    #     # Setup a simple stalemate position
    #     setup_game.reset()
    #     setup_game.add_piece(King(Color.BLACK, "a8"))
    #     setup_game.add_piece(Queen(Color.WHITE, "c7"))
    #     setup_game.add_piece(King(Color.WHITE, "c6"))
    #     setup_game.active_player = Color.BLACK
    #     setup_game.move('a8', 'a7')  # Black king has no legal moves but is not in check
    #     black_king = setup_game.get_king(Color.BLACK)
    #     assert black_king.check_for_stalemate() is True
    #
    # def test_threefold_repetition(self, setup_game):
    #     # Repeat the same position three times
    #     setup_game.active_player = Color.WHITE
    #     setup_game.move('b1', 'c3')
    #     setup_game.active_player = Color.BLACK
    #     setup_game.move('b8', 'c6')
    #     setup_game.active_player = Color.WHITE
    #     setup_game.move('c3', 'b1')
    #     setup_game.active_player = Color.BLACK
    #     setup_game.move('c6', 'b8')
    #     setup_game.active_player = Color.WHITE
    #     setup_game.move('b1', 'c3')
    #     setup_game.active_player = Color.BLACK
    #     setup_game.move('b8', 'c6')
    #     setup_game.active_player = Color.WHITE
    #     setup_game.move('c3', 'b1')
    #     setup_game.active_player = Color.BLACK
    #     setup_game.move('c6', 'b8')
    #     # The position has been repeated three times
    #     assert setup_game.is_threefold_repetition()
    #
    # def test_fifty_move_rule(self, setup_game):
    #     # Make 50 moves without any pawn movement or capture
    #     for _ in range(25):
    #         setup_game.active_player = Color.WHITE
    #         setup_game.move('b1', 'c3')
    #         setup_game.active_player = Color.BLACK
    #         setup_game.move('b8', 'c6')
    #         setup_game.active_player = Color.WHITE
    #         setup_game.move('c3', 'b1')
    #         setup_game.active_player = Color.BLACK
    #         setup_game.move('c6', 'b8')
    #     # The 50-move rule should now be in effect
    #     assert setup_game.is_fifty_move_rule()

    # Object Creation Tests
    def test_pawn_initialization(self, setup_game):
        pawn = Pawn(Color.WHITE, "a2")
        assert isinstance(pawn, Pawn) and pawn.color == Color.WHITE and pawn.location == "a2" and pawn.points == 1

    # Board Initialization Tests
    def test_board_initialization(self, setup_game):
        assert isinstance(setup_game.board['a2'], Pawn)
        assert isinstance(setup_game.board['b1'], Knight)

    # Piece Movement Tests
    def test_white_pawn_movement(self, setup_game):
        pawn = setup_game.board['a2']
        setup_game.move('a2', 'a4')
        assert str(pawn.location) == 'a4'
        assert setup_game.board['a4'] is pawn
        assert setup_game.board['a2'] is None
        with pytest.raises(Game.MoveException):
            setup_game.move('a4', 'a6')
        setup_game.active_player = Color.WHITE
        setup_game.move('a4', 'a5')
        assert str(pawn.location) == 'a5' and setup_game.board['a5'] is pawn and setup_game.board['a4'] is None

        setup_game.active_player = Color.WHITE
        # Pick the white pawn at b2
        pawn = setup_game.board['b2']
        pawn_clone = deepcopy(pawn)
        # Try a bunch of illgal moves
        with pytest.raises(Game.MoveException):
            setup_game.move('b2', 'a6')
            setup_game.move('b2', 'b6')
            setup_game.move('b2', 'u8')
            setup_game.move('b2', 'z2')
            setup_game.move('b2', 'xx')
            setup_game.move('b2', '22')
            setup_game.move('b2', '923')
            setup_game.move('b2', 'abc')
            setup_game.move('b2', "knight to queen's bishop")

        assert pawn == pawn_clone and pawn.location == 'b2'
        setup_game.active_player = Color.WHITE
        setup_game.move('b2', 'b4')
        assert pawn.location == 'b4'
        setup_game.active_player = Color.BLACK
        setup_game.move('h7', 'h6')
        assert pawn.location == 'b4' and setup_game.board['b4'] is pawn and setup_game.board['b2'] is None
        # Confirm that we can't move backwards
        with pytest.raises(Game.MoveException):
            setup_game.move('b4', 'b3')

    def test_black_pawn_movement(self, setup_game):
        setup_game.active_player = Color.BLACK
        pawn = setup_game.board['a7']
        setup_game.active_player = Color.BLACK
        setup_game.move('a7', 'a5')
        assert pawn.location == 'a5' and setup_game.board['a5'] is pawn and setup_game.board['a7'] is None
        with pytest.raises(Game.MoveException):
            setup_game.move('a5', 'a3')
        setup_game.active_player = Color.BLACK
        setup_game.move('a5', 'a4')
        assert pawn.location == 'a4' and setup_game.board['a4'] is pawn and setup_game.board['a5'] is None
        pawn = setup_game.board['b7']
        setup_game.active_player = Color.BLACK
        with pytest.raises(Game.MoveException):
            setup_game.move('b7', 'a6')
            setup_game.move('b7', 'b1')
            setup_game.move('b7', 'u8')
            setup_game.move('b7', 'z2')
            setup_game.move('b7', 'xx')
            setup_game.move('b7', '22')
            setup_game.move('b7', '923')
            setup_game.move('b7', 'abc')
            setup_game.move('b7', "knight to queen's bishop")
        setup_game.active_player = Color.BLACK
        setup_game.move('b7', 'b5')
        assert pawn.location == 'b5' and setup_game.board['b5'] is pawn and setup_game.board['b7'] is None
        with pytest.raises(Game.MoveException):
            setup_game.move('b5', 'b3')

    def test_knight_movement(self, setup_game):
        try_movements('b1', ["c3", "b5", "a3", "b1"], setup_game)

    # Test Bishop Movements
    def test_bishop_movement(self, setup_game):
        setup_game.reset()
        bishop = Bishop(Color.WHITE, "c1")
        setup_game.board['c1'] = bishop
        setup_game.move('c1', 'a3')
        assert bishop.location == "a3" and setup_game.board["a3"] is bishop
        # Add additional assertions for invalid moves and black bishop

    # Test Rook Movements
    def test_rook_movement(self, setup_game):
        setup_game.reset()
        rook = Rook(Color.WHITE, "a1")
        setup_game.board['a1'] = rook
        setup_game.move('a1', 'a4')
        assert rook.location == "a4" and setup_game.board["a4"] is rook
        # Add additional assertions for invalid moves and black rook

    # Test Queen Movements
    def test_queen_movement(self, setup_game):
        setup_game.reset()
        queen = Queen(Color.WHITE, "d1")
        setup_game.board['d1'] = queen
        setup_game.move('d1', 'd3')
        assert queen.location == "d3" and setup_game.board["d3"] is queen
        # Add additional assertions for diagonal, horizontal moves and black queen

    # Test King Movements
    def test_king_movement(self, setup_game):
        setup_game.reset()
        king = King(Color.WHITE, "e1")
        setup_game.board['e1'] = king
        setup_game.move('e1', 'e2')
        assert king.location == "e2" and setup_game.board["e2"] is king
        # Add additional assertions for invalid moves and black king

    # Boundary and Exception Tests
    def test_out_of_bounds_movement(self, setup_game):
        pawn = setup_game.board['a2']
        setup_game.board['a2'] = pawn
        with pytest.raises(Location.LocationException):
            setup_game.move('a2', 'a9')

    # Capture Mechanics Tests
    def test_basic_capture_mechanics(self, setup_game):
        setup_game.add_piece(piece=Pawn(Color.BLACK, location="b3"))  # Setup a black pawn
        white_pawn = setup_game.board['a2']
        setup_game.move('a2', 'b3')  # White pawn captures black pawn
        assert white_pawn.location == 'b3', "The white pawn's location has not been updated"
        assert isinstance(setup_game.captured_pieces[Color.BLACK][0], Pawn)
        assert setup_game.captured_pieces[Color.BLACK][0].color == Color.BLACK

    def test_get_intermediate_squares(self):
        assert list(Board.get_intermediate_squares('a2', 'a5')) == ['a3', 'a4']
        assert list(Board.get_intermediate_squares('a1', 'a8')) == ['a2', 'a3', 'a4', 'a5', 'a6', 'a7']
        assert list(Board.get_intermediate_squares('a1', 'h8')) == ['b2', 'c3', 'd4', 'e5', 'f6', 'g7']
        assert list(Board.get_intermediate_squares('a1', 'd4')) == ['b2', 'c3']
        assert list(Board.get_intermediate_squares('a1', 'h1')) == ['b1', 'c1', 'd1', 'e1', 'f1', 'g1']

    def test_extended_capture_mechanics(self, setup_game):
        # Setting up black and white pawns
        setup_game.add_piece(Pawn(Color.BLACK, "b3"))
        setup_game.add_piece(Pawn(Color.BLACK, "c3"))
        setup_game.add_piece(Pawn(Color.BLACK, "d3"))
        setup_game.add_piece(Pawn(Color.BLACK, "e3"))

        # Setting up other black pieces
        setup_game.add_piece(Knight(Color.BLACK, "c6"))
        setup_game.add_piece(Bishop(Color.BLACK, "f6"))

        # White pawn captures black pawn
        white_pawn = setup_game.board['a2']
        setup_game.move('a2', 'b3')
        assert white_pawn.location == 'b3' and isinstance(setup_game.captured_pieces[Color.BLACK][0], Pawn) and setup_game.captured_pieces[Color.BLACK][0].color == Color.BLACK

        setup_game.move('h7', 'h6')

        # White pawn captures another black pawn
        pawn_b2 = setup_game.board['b2']
        setup_game.active_player = Color.WHITE
        setup_game.move('b2', 'c3')
        assert pawn_b2.location == 'c3' and isinstance(setup_game.captured_pieces[Color.BLACK][1], Pawn) and setup_game.captured_pieces[Color.BLACK][1].color == Color.BLACK

        # White knight capturing black pawn
        setup_game.add_piece(Knight(Color.WHITE, "d5"))
        knight_d5 = setup_game.board['d5']
        setup_game.active_player = Color.WHITE
        setup_game.move('d5', 'e3')
        assert knight_d5.location == 'e3' and isinstance(setup_game.captured_pieces[Color.BLACK][2], Pawn) and setup_game.captured_pieces[Color.BLACK][2].color == Color.BLACK

    def test_game_simulation_with_captures(self, setup_game):
        # Move white pawn from e2 to e4
        make_move(setup_game, 'e2', 'e4')
        # Move black pawn from d7 to d5
        make_move(setup_game, 'd7', 'd5')
        # White pawn captures black pawn
        make_move(setup_game, 'e4', 'd5')
        # Move black knight from b8 to c6
        make_move(setup_game, 'b8', 'c6')
        # Move white bishop from f1 to c4
        make_move(setup_game, 'f1', 'c4')
        # Move black pawn from e7 to e6
        make_move(setup_game, 'e7', 'e6')
        # Move white knight from g1 to f3
        make_move(setup_game, 'g1', 'f3')

    def test_tempmove(self, setup_game):
        original_board = deepcopy(setup_game.board)
        with Board.TempMove(setup_game):
            setup_game.move("b2", "b4")
            assert setup_game.board['b4'] == Pawn(Color.WHITE, 'b4')
            assert setup_game.board['b2'] is None

            setup_game.move("e7", "e5")
            assert setup_game.board['e5'] == Pawn(Color.BLACK, 'e5')
            assert setup_game.board['e7'] is None

            setup_game.move("g1", "f3")
            assert setup_game.board['f3'] == Knight(Color.WHITE, 'f3')
            assert setup_game.board['g1'] is None

            # Bishop takes Pawn
            setup_game.move("f8", "b4")
            assert setup_game.board['b4'] == Bishop(Color.BLACK, 'b4')
            assert setup_game.board['f8'] is None

            assert setup_game.captured_pieces == {Color.WHITE: [Pawn(Color.WHITE, None)], Color.BLACK: []}
            assert len(setup_game.pieces[Color.WHITE]) == 15

        assert setup_game.board['b2'] == Pawn(Color.WHITE, 'b2')
        assert setup_game.board['b4'] is None
        assert setup_game.captured_pieces == {Color.WHITE: [], Color.BLACK: []}
        assert len(setup_game.pieces[Color.WHITE]) == 16
