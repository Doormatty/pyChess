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
    def test_game(self):
        game = Game()
        game.reset()
        game.setup_board()
        return game

    # Edge Case Tests
    def test_pawn_promotion(self, test_game):
        # Move white pawn to the last rank
        test_game.reset()
        test_game.add_piece(Pawn(Color.WHITE, "a7"))
        test_game.active_player = Color.WHITE
        test_game.move('a7', 'a8')
        test_game.promote_pawn('a8', 'Queen')
        # Ensure pawn is promoted to a queen by default
        assert isinstance(test_game.board['a8'], Queen)
        assert test_game.board['a8'].color == Color.WHITE

    def test_en_passant_capture(self, test_game):
        # Simulate the conditions for en passant
        test_game.reset()
        test_game.add_piece(Pawn(Color.WHITE, "e5"))
        test_game.add_piece(Pawn(Color.BLACK, "d7"))
        test_game.active_player = Color.BLACK
        test_game.move('d7', 'd5')
        # Perform en passant capture
        test_game.active_player = Color.WHITE
        test_game.move('e5', 'd6')
        assert test_game.board['d6'] == Pawn(Color.WHITE, 'd6')
        assert test_game.board['d5'] is None
        assert isinstance(test_game.captured_pieces[Color.BLACK][-1], Pawn)

    def test_castling_success(self, test_game):
        # Clear the path for castling
        test_game._remove_piece_at_square('f1')
        test_game._remove_piece_at_square('g1')
        test_game._remove_piece_at_square('f8')
        test_game._remove_piece_at_square('g8')
        # Test kingside castling
        test_game.active_player = Color.WHITE
        test_game.move('O-O', None)
        assert isinstance(test_game.board['g1'], King)
        assert isinstance(test_game.board['f1'], Rook)
        test_game.active_player = Color.BLACK
        test_game.move('O-O', None)
        assert isinstance(test_game.board['g8'], King)
        assert isinstance(test_game.board['f8'], Rook)
        test_game.setup_board()
        # Perform queenside castling
        test_game._remove_piece_at_square('d1')
        test_game._remove_piece_at_square('c1')
        test_game._remove_piece_at_square('b1')
        test_game._remove_piece_at_square('d8')
        test_game._remove_piece_at_square('c8')
        test_game._remove_piece_at_square('b8')
        test_game.active_player = Color.WHITE
        test_game.move('O-O-O', None)
        assert isinstance(test_game.board['c1'], King)
        assert isinstance(test_game.board['d1'], Rook)
        test_game.active_player = Color.BLACK
        test_game.move('O-O-O', None)
        assert isinstance(test_game.board['c8'], King)
        assert isinstance(test_game.board['d8'], Rook)

    def test_castling_failure(self, test_game):
        # Clear the path for castling
        test_game._remove_piece_at_square('g1')
        test_game._remove_piece_at_square('g8')
        # Test kingside castling
        test_game.active_player = Color.WHITE
        with pytest.raises(Game.MoveException):
            test_game.move('O-O', None)

            test_game.active_player = Color.BLACK
        with pytest.raises(Game.MoveException):
            test_game.move('O-O', None)

        test_game.setup_board()
        # Perform queenside castling
        test_game._remove_piece_at_square('d1')
        test_game._remove_piece_at_square('b1')
        test_game._remove_piece_at_square('d8')
        test_game._remove_piece_at_square('b8')

        test_game.active_player = Color.WHITE
        with pytest.raises(Game.MoveException):
            test_game.move('O-O-O', None)
        test_game.active_player = Color.BLACK
        with pytest.raises(Game.MoveException):
            test_game.move('O-O-O', None)

    def test_castling_failure_due_to_check(self, test_game):
        # Now check that we can't castle when one square is in check
        test_game.reset()
        test_game.add_piece(Rook(Color.BLACK, "a8"))
        test_game.add_piece(King(Color.BLACK, "e8"))
        test_game.add_piece(Rook(Color.BLACK, "h8"))
        test_game.add_piece(Queen(Color.WHITE, "b5"))
        test_game.add_piece(King(Color.WHITE, "e1"))

        test_game.active_player = Color.BLACK
        with pytest.raises(Game.MoveException):
            test_game.move('O-O-O', None)
        with pytest.raises(Game.MoveException):
            test_game.move('O-O', None)

        # Now check that we can't castle when one intermediate square is in check
        test_game.reset()
        test_game.add_piece(Rook(Color.BLACK, "a8"))
        test_game.add_piece(King(Color.BLACK, "e8"))
        test_game.add_piece(Rook(Color.BLACK, "h8"))
        test_game.add_piece(Queen(Color.WHITE, "f4"))
        test_game.add_piece(King(Color.WHITE, "e1"))

        test_game.active_player = Color.BLACK
        # Confirm that Castling kingside is verboten, but Queenside is possible
        with pytest.raises(Game.MoveException):
            test_game.move('O-O', None)
        test_game.move('O-O-O', None)

    def test_checkmate_detection(self, test_game):
        # Setup a simple checkmate position
        test_game.reset()
        test_game.add_piece(King(Color.BLACK, "a8"))
        test_game.add_piece(Queen(Color.WHITE, "b6"))
        test_game.add_piece(King(Color.WHITE, "c6"))
        test_game.active_player = Color.WHITE
        assert test_game.check_for_checkmate() is True

    # def test_stalemate_detection(self, test_game):
    #     # Setup a simple stalemate position
    #     test_game.reset()
    #     test_game.add_piece(King(Color.BLACK, "a8"))
    #     test_game.add_piece(Queen(Color.WHITE, "c7"))
    #     test_game.add_piece(King(Color.WHITE, "c6"))
    #     test_game.active_player = Color.BLACK
    #     test_game.move('a8', 'a7')  # Black king has no legal moves but is not in check
    #     black_king = test_game.get_king(Color.BLACK)
    #     assert black_king.check_for_stalemate() is True
    #
    # def test_threefold_repetition(self, test_game):
    #     # Repeat the same position three times
    #     test_game.active_player = Color.WHITE
    #     test_game.move('b1', 'c3')
    #     test_game.active_player = Color.BLACK
    #     test_game.move('b8', 'c6')
    #     test_game.active_player = Color.WHITE
    #     test_game.move('c3', 'b1')
    #     test_game.active_player = Color.BLACK
    #     test_game.move('c6', 'b8')
    #     test_game.active_player = Color.WHITE
    #     test_game.move('b1', 'c3')
    #     test_game.active_player = Color.BLACK
    #     test_game.move('b8', 'c6')
    #     test_game.active_player = Color.WHITE
    #     test_game.move('c3', 'b1')
    #     test_game.active_player = Color.BLACK
    #     test_game.move('c6', 'b8')
    #     # The position has been repeated three times
    #     assert test_game.is_threefold_repetition()
    #
    # def test_fifty_move_rule(self, test_game):
    #     # Make 50 moves without any pawn movement or capture
    #     for _ in range(25):
    #         test_game.active_player = Color.WHITE
    #         test_game.move('b1', 'c3')
    #         test_game.active_player = Color.BLACK
    #         test_game.move('b8', 'c6')
    #         test_game.active_player = Color.WHITE
    #         test_game.move('c3', 'b1')
    #         test_game.active_player = Color.BLACK
    #         test_game.move('c6', 'b8')
    #     # The 50-move rule should now be in effect
    #     assert test_game.is_fifty_move_rule()

    # Object Creation Tests
    def test_pawn_initialization(self, test_game):
        pawn = Pawn(Color.WHITE, "a2")
        assert isinstance(pawn, Pawn) and pawn.color == Color.WHITE and pawn.location == "a2" and pawn.points == 1

    # Board Initialization Tests
    def test_board_initialization(self, test_game):
        assert isinstance(test_game.board['a2'], Pawn)
        assert isinstance(test_game.board['b1'], Knight)

    # Piece Movement Tests
    def test_white_pawn_movement(self, test_game):
        pawn = test_game.board['a2']
        test_game.move('a2', 'a4')
        assert str(pawn.location) == 'a4'
        assert test_game.board['a4'] is pawn
        assert test_game.board['a2'] is None
        with pytest.raises(Game.MoveException):
            test_game.move('a4', 'a6')
        test_game.active_player = Color.WHITE
        test_game.move('a4', 'a5')
        assert str(pawn.location) == 'a5' and test_game.board['a5'] is pawn and test_game.board['a4'] is None

        test_game.active_player = Color.WHITE
        # Pick the white pawn at b2
        pawn = test_game.board['b2']
        pawn_clone = deepcopy(pawn)
        # Try a bunch of illgal moves
        with pytest.raises(Game.MoveException):
            test_game.move('b2', 'a6')
            test_game.move('b2', 'b6')
            test_game.move('b2', 'u8')
            test_game.move('b2', 'z2')
            test_game.move('b2', 'xx')
            test_game.move('b2', '22')
            test_game.move('b2', '923')
            test_game.move('b2', 'abc')
            test_game.move('b2', "knight to queen's bishop")

        assert pawn == pawn_clone and pawn.location == 'b2'
        test_game.active_player = Color.WHITE
        test_game.move('b2', 'b4')
        assert pawn.location == 'b4'
        test_game.active_player = Color.BLACK
        test_game.move('h7', 'h6')
        assert pawn.location == 'b4' and test_game.board['b4'] is pawn and test_game.board['b2'] is None
        # Confirm that we can't move backwards
        with pytest.raises(Game.MoveException):
            test_game.move('b4', 'b3')

    def test_black_pawn_movement(self, test_game):
        test_game.active_player = Color.BLACK
        pawn = test_game.board['a7']
        test_game.active_player = Color.BLACK
        test_game.move('a7', 'a5')
        assert pawn.location == 'a5' and test_game.board['a5'] is pawn and test_game.board['a7'] is None
        with pytest.raises(Game.MoveException):
            test_game.move('a5', 'a3')
        test_game.active_player = Color.BLACK
        test_game.move('a5', 'a4')
        assert pawn.location == 'a4' and test_game.board['a4'] is pawn and test_game.board['a5'] is None
        pawn = test_game.board['b7']
        test_game.active_player = Color.BLACK
        with pytest.raises(Game.MoveException):
            test_game.move('b7', 'a6')
            test_game.move('b7', 'b1')
            test_game.move('b7', 'u8')
            test_game.move('b7', 'z2')
            test_game.move('b7', 'xx')
            test_game.move('b7', '22')
            test_game.move('b7', '923')
            test_game.move('b7', 'abc')
            test_game.move('b7', "knight to queen's bishop")
        test_game.active_player = Color.BLACK
        test_game.move('b7', 'b5')
        assert pawn.location == 'b5' and test_game.board['b5'] is pawn and test_game.board['b7'] is None
        with pytest.raises(Game.MoveException):
            test_game.move('b5', 'b3')

    def test_knight_movement(self, test_game):
        try_movements('b1', ["c3", "b5", "a3", "b1"], test_game)

    # Test Bishop Movements
    def test_bishop_movement(self, test_game):
        test_game.reset()
        test_game.add_piece(Bishop(Color.WHITE, "c1"))
        try_movements('c1', ["a3", "f8", "h6", "c1", "b2", "g7", "e5"], test_game)
        test_game.reset()
        test_game.add_piece(Bishop(Color.BLACK, "c8"))
        try_movements('c8', ["a6", "f1", "g2", "c6"], test_game)

    # Test Rook Movements
    def test_rook_movement(self, test_game):
        test_game.reset()
        test_game.add_piece(Rook(Color.WHITE, "a1"))
        rook = test_game.board['a1']
        test_game.move('a1', 'a4')
        assert rook.location == "a4" and test_game.board["a4"] is rook
        # Add additional assertions for invalid moves and black rook

    # Test Queen Movements
    def test_queen_movement(self, test_game):
        test_game.reset()
        test_game.add_piece(Queen(Color.WHITE, "d1"))
        queen = test_game.board['d1']
        test_game.move('d1', 'd3')
        assert queen.location == "d3" and test_game.board["d3"] is queen
        # Add additional assertions for diagonal, horizontal moves and black queen

    # Test King Movements
    def test_king_movement(self, test_game):
        test_game.reset()
        test_game.add_piece(King(Color.WHITE, "e1"))
        king = test_game.board['e1']
        test_game.move('e1', 'e2')
        assert king.location == "e2" and test_game.board["e2"] is king
        # Add additional assertions for invalid moves and black king

    # Boundary and Exception Tests
    def test_out_of_bounds_movement(self, test_game):
        pawn = test_game.board['a2']
        test_game.board['a2'] = pawn
        with pytest.raises(Location.LocationException):
            test_game.move('a2', 'a9')

    # Capture Mechanics Tests
    def test_basic_capture_mechanics(self, test_game):
        test_game.add_piece(piece=Pawn(Color.BLACK, location="b3"))  # Setup a black pawn
        white_pawn = test_game.board['a2']
        test_game.move('a2', 'b3')  # White pawn captures black pawn
        assert white_pawn.location == 'b3', "The white pawn's location has not been updated"
        assert isinstance(test_game.captured_pieces[Color.BLACK][0], Pawn)
        assert test_game.captured_pieces[Color.BLACK][0].color == Color.BLACK

    def test_get_intermediate_squares(self):
        assert list(Board.get_intermediate_squares('a2', 'a5')) == ['a3', 'a4']
        assert list(Board.get_intermediate_squares('a1', 'a8')) == ['a2', 'a3', 'a4', 'a5', 'a6', 'a7']
        assert list(Board.get_intermediate_squares('a1', 'h8')) == ['b2', 'c3', 'd4', 'e5', 'f6', 'g7']
        assert list(Board.get_intermediate_squares('a1', 'd4')) == ['b2', 'c3']
        assert list(Board.get_intermediate_squares('a1', 'h1')) == ['b1', 'c1', 'd1', 'e1', 'f1', 'g1']

    def test_extended_capture_mechanics(self, test_game):
        # Setting up black and white pawns
        test_game.add_piece(Pawn(Color.BLACK, "b3"))
        test_game.add_piece(Pawn(Color.BLACK, "c3"))
        test_game.add_piece(Pawn(Color.BLACK, "d3"))
        test_game.add_piece(Pawn(Color.BLACK, "e3"))

        # Setting up other black pieces
        test_game.add_piece(Knight(Color.BLACK, "c6"))
        test_game.add_piece(Bishop(Color.BLACK, "f6"))

        # White pawn captures black pawn
        white_pawn = test_game.board['a2']
        test_game.move('a2', 'b3')
        assert white_pawn.location == 'b3' and isinstance(test_game.captured_pieces[Color.BLACK][0], Pawn) and test_game.captured_pieces[Color.BLACK][0].color == Color.BLACK

        test_game.move('h7', 'h6')

        # White pawn captures another black pawn
        pawn_b2 = test_game.board['b2']
        test_game.active_player = Color.WHITE
        test_game.move('b2', 'c3')
        assert pawn_b2.location == 'c3' and isinstance(test_game.captured_pieces[Color.BLACK][1], Pawn) and test_game.captured_pieces[Color.BLACK][1].color == Color.BLACK

        # White knight capturing black pawn
        test_game.add_piece(Knight(Color.WHITE, "d5"))
        knight_d5 = test_game.board['d5']
        test_game.active_player = Color.WHITE
        test_game.move('d5', 'e3')
        assert knight_d5.location == 'e3' and isinstance(test_game.captured_pieces[Color.BLACK][2], Pawn) and test_game.captured_pieces[Color.BLACK][2].color == Color.BLACK

    def test_game_simulation_with_captures(self, test_game):
        # Move white pawn from e2 to e4
        make_move(test_game, 'e2', 'e4')
        # Move black pawn from d7 to d5
        make_move(test_game, 'd7', 'd5')
        # White pawn captures black pawn
        make_move(test_game, 'e4', 'd5')
        # Move black knight from b8 to c6
        make_move(test_game, 'b8', 'c6')
        # Move white bishop from f1 to c4
        make_move(test_game, 'f1', 'c4')
        # Move black pawn from e7 to e6
        make_move(test_game, 'e7', 'e6')
        # Move white knight from g1 to f3
        make_move(test_game, 'g1', 'f3')

    def test_tempmove(self, test_game):
        original_board = deepcopy(test_game.board)
        with Board.TempMove(test_game):
            test_game.move("b2", "b4")
            assert test_game.board['b4'] == Pawn(Color.WHITE, 'b4')
            assert test_game.board['b2'] is None

            test_game.move("e7", "e5")
            assert test_game.board['e5'] == Pawn(Color.BLACK, 'e5')
            assert test_game.board['e7'] is None

            test_game.move("g1", "f3")
            assert test_game.board['f3'] == Knight(Color.WHITE, 'f3')
            assert test_game.board['g1'] is None

            # Bishop takes Pawn
            test_game.move("f8", "b4")
            assert test_game.board['b4'] == Bishop(Color.BLACK, 'b4')
            assert test_game.board['f8'] is None

            assert test_game.captured_pieces == {Color.WHITE: [Pawn(Color.WHITE, None)], Color.BLACK: []}
            assert len(test_game.pieces[Color.WHITE]) == 15

        assert test_game.board['b2'] == Pawn(Color.WHITE, 'b2')
        assert test_game.board['b4'] is None
        assert test_game.captured_pieces == {Color.WHITE: [], Color.BLACK: []}
        assert len(test_game.pieces[Color.WHITE]) == 16
