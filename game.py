import logging
import re
from copy import deepcopy

from rich.console import Console
from rich.logging import RichHandler

from board import Board
from pieces import Pawn, Rook, Bishop, Knight, Queen, King, Piece
from utils import Color, Location


class Game:
    class MoveException(Exception):
        pass

    def __init__(self, loglevel='INFO'):
        self.console = Console()
        self.board = Board(console=self.console)
        self.pieces = {Color.WHITE: [], Color.BLACK: []}
        self.captured_pieces = {Color.WHITE: [], Color.BLACK: []}
        self.turn_number = 0
        self.moves = []
        self.halfmove_counter = 0
        self.enpassants = None
        self.castling = []
        self.active_player = Color.WHITE
        self.setup_board()
        logging.basicConfig(level=loglevel, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True, console=self.console, markup=True, show_path=False)])
        self.logger = logging.getLogger("rich")
        self.logger.setLevel(loglevel)

    @property
    def antiplayer(self):
        return Color.BLACK if self.active_player == Color.WHITE else Color.WHITE

    def reset(self):
        """
        Clear the Game, and wipe the board
        """
        self.board.clear()
        self.pieces = {Color.WHITE: [], Color.BLACK: []}
        self.captured_pieces = {Color.WHITE: [], Color.BLACK: []}
        self.turn_number = 0
        self.moves = []
        self.halfmove_counter = 0
        self.enpassants = []
        self.castling = []
        self.active_player = Color.WHITE

    def setup_board(self):
        """
        Clear the Game, and wipe the board, then initialize the board with a standard set of pieces.
        """

        self.board.clear()
        self.reset()

        for square in self.board.iter_square_names():
            row = square[1]
            col = square[0]

            if row in ('3', '4', '5', '6'):
                self.board.squares[square] = None
            elif row == '2':
                self.add_piece(piece=Pawn(Color.WHITE, location=square))
            elif row == '7':
                self.add_piece(piece=Pawn(Color.BLACK, location=square))
            elif row in ('1', '8'):
                color = Color.WHITE if row == '1' else Color.BLACK
                if col in ('a', 'h'):
                    self.add_piece(piece=Rook(color, location=square))
                elif col in ('b', 'g'):
                    self.add_piece(piece=Knight(color, location=square))
                elif col in ('c', 'f'):
                    self.add_piece(piece=Bishop(color, location=square))
                elif col == 'd':
                    self.add_piece(piece=Queen(color, location=square))
                elif col == 'e':
                    self.add_piece(piece=King(color, location=square))

    def add_piece(self, piece):
        self.pieces[piece.color].append(piece)
        self.board.add_piece(piece=piece)

    def get_king(self, color):
        return [piece for piece in self.pieces[color] if piece.__class__.__name__ == 'King'][0]

    def move(self, start: Location | str, end: Location | str | None):
        if start in ("O-O", "O-O-O"):
            self.handle_castling(start)
            return
        start = Location(start) if isinstance(start, str) else start
        end = Location(end) if isinstance(end, str) else end

        # Ensure there is a piece at the start location
        if self.board[start] is None:
            raise Game.MoveException(f"No piece at {start}")

        # Determine if the move is a capture or a standard move
        if end == self.enpassants:
            # Handle en passant capture
            captured_piece = self.handle_enpassant(start, end)
        else:
            if self.board[end] is not None:
                # Handle regular capture
                if not self.board[start].can_take(end, self):
                    raise Game.MoveException(f"{self.board[start].string()} at {start} cannot capture {self.board[end].string()} at {end}")
                captured_piece = self.board[end]
                captured_piece.location = None  # Remove captured piece from the board
                self.enpassants = None
            else:
                # Handle non-capture move
                if not self.board[start].can_move_to(end, self):
                    raise Game.MoveException(f"{self.board[start].string()} at {start} can't move to {end}")
                captured_piece = None

            # Move the piece
            self.board[end] = self.board[start]
            self.board[start] = None
            self.move_effects(start, end)

        if captured_piece:
            self.captured_pieces[captured_piece.color].append(captured_piece)
            self.pieces[captured_piece.color].remove(captured_piece)
            self.finalize_move(start=start, end=end)

    def move_effects(self, start: Location, end: Location | None = None):
        if self.board[end] is None:
            raise Game.MoveException(f"No piece at {end} to apply move effects to.")
        self.board[end].move_effects(start=start, end=end, game=self)

    def describe_move(self, parsed_move) -> str:
        move = parsed_move['move']
        if move in ("O-O", "O-O-O"):
            if move == "O-O-O":
                return f"{self.active_player.value}: castles Queenside"
            else:
                return f"{self.active_player.value}: castles Kingside"

        if parsed_move['capture']:
            return f"{self.active_player.value}: {parsed_move['start_square']} to {parsed_move['end_square']}, {self.board.squares[parsed_move['start_square']].__class__.__name__} takes {self.board.squares[parsed_move['end_square']].__class__.__name__}"
        else:
            return f"{self.active_player.value}: {parsed_move['start_square']} to {parsed_move['end_square']}"

    def compact_move(self, move: str):
        parsed_move = self.parse_move(move)
        capture = parsed_move['capture']
        # self.logger.debug(f"Parsed {move} into {parsed_move}")
        expanded_move = self.expand_move(parsed_move)
        if move in ("O-O", "O-O-O"):
            self.move(move, None)
            self.logger.info(self.describe_move(parsed_move))
        else:
            parsed_move['start_square'] = expanded_move[0]
            parsed_move['end_square'] = expanded_move[1]
            description = self.describe_move(parsed_move)
            try:
                if len(expanded_move) == 3:
                    self.move(start=expanded_move[0], end=expanded_move[1])
                else:
                    self.move(start=expanded_move[0], end=expanded_move[1])
            except self.MoveException as e:
                self.logger.error(e)
                raise
            else:
                self.logger.info(description)

    @staticmethod
    def parse_move(move: str) -> dict:
        pattern = r'((?P<start_type>[KQNBR])?(?P<start_square>[a-h][1-8]?)?(?P<capture>x)?(?P<end_type>[KQNBR])?(?P<end_square>[a-h][1-8])=?(?P<promotion>[KQNBR])?(?P<check>\+)?)?(?P<kscastle>O-O)?(?P<qscastle>O-O-O)?(?P<checkmate>#)?'
        parts = re.match(pattern, move)
        type_dict = {'K': King, 'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight}
        return {'move': move,
                'start_type': type_dict[parts['start_type']] if parts['start_type'] is not None else Pawn,
                'end_type': type_dict[parts['end_type']] if parts['end_type'] is not None else None,
                'start_square': parts['start_square'],
                'end_square': parts['end_square'],
                'promotion': parts['promotion'] if parts['promotion'] else False,
                'capture': True if parts['capture'] else False,
                'check': True if parts['check'] else False,
                'checkmate': True if parts['checkmate'] else False,
                'king_castle': True if parts['kscastle'] else False,
                'queen_castle': True if parts['qscastle'] else False}

    def expand_move(self, parsed_move) -> tuple[str, str | None] | tuple[str, str | None, str]:
        if parsed_move['king_castle'] or parsed_move['queen_castle']:
            return parsed_move, None

        start_square, end_square = self.determine_start_and_end_squares(parsed_move)
        possibles = self.find_possible_moves(parsed_move, start_square, end_square)
        possibles_after_self_check = [p for p in possibles if not self.does_move_cause_self_check(p.location, end_square)]

        if len(possibles_after_self_check) > 1:
            raise self.MoveException(self, f"Ambiguous move: {parsed_move['move']} could refer to multiple pieces.")
        if not possibles_after_self_check:
            raise self.MoveException(self, f"No moves found for {parsed_move['move']} after running self-check detection, but had found {possibles}")
        return possibles_after_self_check[0].location, end_square

    def determine_start_and_end_squares(self, parsed_move):
        start_square = parsed_move['start_square']
        end_square = parsed_move['end_square']
        if parsed_move['start_type'].__qualname__ == 'King' and start_square is None:
            start_square = self.find_king_location(self.active_player)
        return start_square, end_square

    def find_possible_moves(self, parsed_move, start_square, end_square):
        if parsed_move['capture']:
            return self.find_possible_captures(parsed_move, start_square, end_square)
        else:
            return self.who_can_move_to(location=end_square, color_filter=self.active_player, piece_filter=parsed_move['start_type'].__qualname__, file_filter=start_square[0] if start_square else None)

    def find_possible_captures(self, parsed_move, start_square, end_square):
        if end_square in self.enpassants and parsed_move['start_type'].__qualname__ == 'Pawn' and self.board[end_square] is None:
            return self.handle_enpassant_possibility(parsed_move, start_square, end_square)
        elif self.board[end_square] is None:
            raise self.MoveException(self, f"Illegal capture: no piece at {end_square}.")
        return self.who_can_capture(end_square, parsed_move['start_type'].__qualname__, start_square[0] if start_square else None, self.antiplayer)

    def does_move_cause_self_check(self, start, end):
        with self.board.TempMove(self):
            self.move(start, end)
            is_check = self.is_king_in_check(self.active_player)
            if is_check:
                self.is_king_in_check(self.active_player)
            return is_check

    def finalize_move(self, start, end):
        self.moves.append((f"{start} {end}", (self.board[start], self.board[end])))
        self.active_player = Color.BLACK if self.active_player == Color.WHITE else Color.WHITE
        self.check_for_checkmate()
        if self.active_player == Color.WHITE:
            self.turn_number += 1

    def promote_pawn(self, location, new_type):
        piece = self.board[location]
        if piece is None or not isinstance(piece, Pawn):
            raise self.MoveException(self, f"Cannot promote piece at {location}, it is not a pawn")
        if not ((piece.location[1] == "8" and piece.color == Color.WHITE) or (piece.location[1] == "1" and piece.color == Color.BLACK)):
            raise self.MoveException(self, f"Can only promote pawns in the end row")
        self.board[location] = None
        self.pieces[piece.color].remove(piece)
        new_piece = globals()[new_type](piece.color, location)
        self.add_piece(new_piece)
        self.pieces[piece.color].append(new_piece)
        self.board[location] = new_piece

    def handle_castling(self, special):
        self.castle(special)
        self.moves.append(special)
        self.enpassants = []
        if self.active_player == Color.WHITE:
            self.turn_number += 1

    def handle_enpassant(self, start, end) -> Piece:
        capture_rank = '5' if self.active_player == Color.WHITE else '4'
        square_to_capture = f'{end[0]}{capture_rank}'
        captured_piece = deepcopy(self.board[square_to_capture])
        self.board[square_to_capture] = None
        self._force_move(start, end)
        self.captured_pieces[captured_piece.color].append(captured_piece)
        if self.board[end] is not None:
            self.board[end].move_effects(start, end, self.board)
        return captured_piece

    def who_can_move_to(self, location, color_filter=None, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")

        color_filter = color_filter or self.active_player.value
        pieces = []
        for piece in self.pieces[color_filter]:
            if piece_filter is None or piece.__class__.__name__ == piece_filter:
                if file_filter is None or piece.location[0] == file_filter:
                    if piece.can_move_to(location, self):
                        pieces.append(piece)
        return deepcopy(pieces)

    def castle(self, move: str):
        can_castle = self.can_castle()
        if move == "O-O":
            if not can_castle[self.active_player]['kingside']:
                raise self.MoveException(self, f"{self.active_player.value()} cannot castle Kingside.")
            if self.active_player == Color.WHITE:
                self._force_move("e1", "g1")
                self._force_move("h1", "f1")
                self.board["g1"].has_moved = True
                self.board["f1"].has_moved = True
            else:
                self._force_move("e8", "g8")
                self._force_move("h8", "f8")
                self.board["g8"].has_moved = True
                self.board["f8"].has_moved = True
        elif move == "O-O-O":
            if not can_castle[self.active_player]['queenside']:
                raise self.MoveException(self, f"{self.active_player.value} cannot castle Queenside.")
            if self.active_player == Color.WHITE:
                self._force_move("e1", "c1")
                self._force_move("a1", "e1")
                self.board["c1"].has_moved = True
                self.board["e1"].has_moved = True
            else:
                self._force_move("e8", "c8")
                self._force_move("a8", "d8")
                self.board["c8"].has_moved = True
                self.board["d8"].has_moved = True

    def can_castle(self) -> dict:
        retval = {Color.WHITE: {'queenside': False, 'kingside': False}, Color.BLACK: {'queenside': False, 'kingside': False}}
        if self.board['e1'] is not None and not self.board['e1'].has_moved and not self.who_can_capture('e1', color_filter=Color.BLACK):
            retval[Color.WHITE]['queenside'] = (self.board['a1'] is not None and not self.board['a1'].has_moved
                                                and self.board['d1'] is None and not self.who_can_capture('d1', color_filter=Color.BLACK)
                                                and self.board['c1'] is None and not self.who_can_capture('c1', color_filter=Color.BLACK)
                                                and self.board['b1'] is None and not self.who_can_capture('b1', color_filter=Color.BLACK))
            retval[Color.WHITE]['kingside'] = (self.board['h1'] is not None and not self.board['h1'].has_moved
                                               and self.board['f1'] is None and not self.who_can_capture('f1', color_filter=Color.BLACK)
                                               and self.board['g1'] is None and not self.who_can_capture('g1', color_filter=Color.BLACK))
        if self.board['e8'] is not None and not self.board['e8'].has_moved and not self.who_can_capture('e8', color_filter=Color.WHITE):
            retval[Color.BLACK]['queenside'] = (self.board['a8'] is not None and not self.board['a8'].has_moved
                                                and self.board['d8'] is None and not self.who_can_capture('d8', color_filter=Color.WHITE)
                                                and self.board['c8'] is None and not self.who_can_capture('c8', color_filter=Color.WHITE)
                                                and self.board['b8'] is None and not self.who_can_capture('b8', color_filter=Color.WHITE))
            retval[Color.BLACK]['kingside'] = (self.board['h8'] is not None and not self.board['h8'].has_moved
                                               and self.board['f8'] is None and not self.who_can_capture('f8', color_filter=Color.WHITE)
                                               and self.board['g8'] is None and not self.who_can_capture('g8', color_filter=Color.WHITE))
        return retval

    def _force_move(self, start: str, end: str):
        if isinstance(start, Location):
            start = str(start.location)
        if isinstance(end, Location):
            end = str(end.location)
        piece = self.board[start]
        self.board[start] = None
        self.board[end] = piece

    def handle_enpassant_possibility(self, parsed_move, start_square, end_square):
        capture_rank = '6' if self.active_player == Color.WHITE else '3'
        square_to_capture = f'{end_square[0]}{capture_rank}'
        possibles = self.who_can_capture(end_square, 'Pawn', start_square[0] if start_square else None, self.active_player.value)
        if len(possibles) != 1:
            raise self.MoveException(self, "En passant capture ambiguity.")
        return possibles

    def find_king_location(self, player_color):
        return next(piece.location for piece in self.pieces[player_color] if isinstance(piece, King))

    def who_can_capture(self, location, piece_filter=None, file_filter=None, color_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")
        pieces = []
        target = self.board[location]
        if target is not None:
            color_filter = target.anticolor()
        for piece in self.pieces[color_filter]:
            if piece_filter is not None and piece.__class__.__name__ != piece_filter:
                continue
            if file_filter is not None and piece.location[0] not in file_filter:
                continue
            if piece.can_take(location, self):
                pieces.append(piece)
        return deepcopy(pieces)

    def is_king_in_check(self, player):
        king = self.get_king(player)
        attackers = self.who_can_capture(king.location)
        if attackers:
            self.logger.info(f"King's attackers found: {attackers}")
            return True
        return False

    def check_for_checkmate(self):
        try:
            opponent_king = [x for x in self.pieces[self.antiplayer] if isinstance(x, King)][0]
        except IndexError:
            return False
        else:
            if opponent_king.is_checkmate(self):
                return True
        return False

    def export_to_fen(self):
        """
        Export the current game state to FEN (Forsyth–Edwards Notation) string.

        Returns:
        str: The FEN string representing the current game state.
        """
        fen = ""
        for number in range(8, 0, -1):
            empty_count = 0
            for letter in "abcdefgh":
                piece = self.board[f'{letter}{number}']
                if piece is None:
                    empty_count += 1
                elif isinstance(piece, Piece):
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    if piece.__class__.__name__ == "Knight":
                        piece_name = "N"
                    else:
                        piece_name = str(piece.__class__.__name__)[0]
                    if piece.color == Color.WHITE:
                        fen += piece_name.upper()
                    else:
                        fen += piece_name.lower()
            if empty_count > 0:
                fen += str(empty_count)
            if number > 1:
                fen += "/"
        fen += f"{' w' if self.turn_number % 2 == 1 else ' b'} {self.fen_can_castle()}"
        fen += " -"  # En passant target square: This is a square over which a pawn has just passed while moving two squares. If there is no en passant target square, use "-"
        fen += f" {str(self.halfmove_counter)} {str(self.turn_number)}"
        return fen

    def fen_can_castle(self) -> str:
        """
        Translates the output of `self.can_castle()` to Fen castling style

        Returns:
        str: A string representing the castling availability. 'KQkq' means that both kings can castle to both sides.
        '-' means no king can castle anymore.
        """
        can_castle = self.can_castle()
        retval = f'{"K" if can_castle[Color.WHITE]["kingside"] else ""}{"Q" if can_castle[Color.WHITE]["queenside"] else ""}{"k" if can_castle[Color.BLACK]["kingside"] else ""}{"q" if can_castle[Color.BLACK]["queenside"] else ""}'
        if retval == "":
            retval = '-'
        return retval
