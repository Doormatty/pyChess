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
        def __init__(self, message: str, game: 'Game' = None) -> None:
            # super().__init__(message)
            self.message = message
            # if game is not None:
            #     self.game = game
            #     self.game.console.print(self.message)
            #     self.game.console.print(self.game.board.create_board_text())

    def __init__(self, loglevel='DEBUG'):
        self.console = Console()

        self.add_logging_level('TRACE', logging.DEBUG - 5)
        self.loglevel = loglevel.upper()
        logging.basicConfig(level=loglevel, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True, console=self.console, markup=True, show_path=False)])
        self.logger = logging.getLogger("__name__")
        self.logger.setLevel(self.loglevel)
        self.board = Board(console=self.console)
        self.pieces = {Color.WHITE: [], Color.BLACK: []}
        self.captured_pieces = {Color.WHITE: [], Color.BLACK: []}
        self.turn_number = 1
        self.moves = []
        self.halfmove_counter = 0
        self.enpassants = None
        self.castling = []
        self.active_player = Color.WHITE
        self.setup_board()

    @staticmethod
    def add_logging_level(level_name, levelNum, methodName=None):
        """
        Comprehensively adds a new logging level to the `logging` module and the
        currently configured logging class.

        `levelName` becomes an attribute of the `logging` module with the value
        `levelNum`. `methodName` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present

        Example
        -------
        >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
        >>> logging.getLogger(__name__).setLevel("TRACE")
        >>> logging.getLogger(__name__).trace('that worked')
        >>> logging.trace('so did this')
        >>> logging.TRACE
        5

        """
        if not methodName:
            methodName = level_name.lower()

        if hasattr(logging, level_name):
            return  # raise AttributeError('{} already defined in logging module'.format(level_name))
        if hasattr(logging, methodName):
            return  # raise AttributeError('{} already defined in logging module'.format(methodName))
        if hasattr(logging.getLoggerClass(), methodName):
            return  # raise AttributeError('{} already defined in logger class'.format(methodName))

        # This method was inspired by the answers to Stack Overflow post
        # http://stackoverflow.com/q/2183233/2988730, especially
        # http://stackoverflow.com/a/13638084/2988730
        def log_for_level(self, message, *args, **kwargs):
            if self.isEnabledFor(levelNum):
                self._log(levelNum, message, args, **kwargs)

        def log_to_root(message, *args, **kwargs):
            logging.log(levelNum, message, *args, **kwargs)

        logging.addLevelName(levelNum, level_name)
        setattr(logging, level_name, levelNum)
        setattr(logging.getLoggerClass(), methodName, log_for_level)
        setattr(logging, methodName, log_to_root)

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
        self.turn_number = 1
        self.moves = []
        self.halfmove_counter = 0
        self.enpassants = []
        self.castling = []
        self.active_player = Color.WHITE
        self.logger.trace("Finished resetting game board.")

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
        self.logger.trace(f"Finished setting up initial piece positions.")

    def _remove_piece(self, piece):
        # Not CAPTURE, but literally remove.
        # Should never be used outside of testing.
        self.board[piece.location] = None
        for p in self.pieces[piece.color]:
            if p.location == piece.location:
                self.pieces[piece.color].remove(p)

    def _remove_piece_at_square(self, square):
        piece = self.board[square]
        if piece is not None:
            self._remove_piece(piece)
        else:
            raise ValueError(f"No piece found at square {square}")
        return piece

    def add_piece(self, piece):
        self.pieces[piece.color].append(piece)
        self.board.add_piece(piece=piece)

    def get_king(self, color):
        return [piece for piece in self.pieces[color] if piece.__class__.__name__ == 'King'][0]

    def move(self, start: Location | str, end: Location | str | None):
        if start in ("O-O", "O-O-O"):
            self.castle(start)
            self.logger.info(f"Turn {self.turn_number}-{self.active_player.value.capitalize()}: Castles {'kingside' if start == 'O-O' else 'queenside'}")
            self.finalize_move(start, None)
            return
        start = Location(start) if isinstance(start, str) else start
        end = Location(end) if isinstance(end, str) else end
        piece_piece = None
        for x in self.pieces[self.active_player]:
            if x.location == start:
                piece_piece = x
        # if piece_piece is None:
        #     raise Game.MoveException('This should never happen!!!', self)
        # Ensure there is a piece at the start location
        if self.board[start] is None:
            raise Game.MoveException(f"No piece at {start}", self)

        # Determine if the move is a capture or a standard move
        if end == self.enpassants:
            # Handle en passant capture
            captured_piece = self.handle_enpassant(start, end)
        else:
            if self.board[end] is not None:
                # Handle regular capture
                if not self.board[start].can_take(end, self):
                    raise Game.MoveException(f"{self.board[start].string()} at {start} cannot capture {self.board[end].string()} at {end}", self)
                captured_piece = self.board[end]
                self.logger.info(f"{self.board[start]} captures {self.board[end]}")
                # captured_piece.location = None  # Remove captured piece from the board
                self.enpassants = None
            else:
                # Handle non-capture move
                if not self.board[start].can_move_to(end, self):
                    raise Game.MoveException(f"{self.board[start].string()} at {start} can't move to {end}", self)
                captured_piece = None

            # Move the piece
            self.board[end] = self.board[start]
            self.board[start] = None
            self.move_effects(start, end)

        if captured_piece:
            self.captured_pieces[captured_piece.color].append(captured_piece)
            for piece in self.pieces[captured_piece.color]:
                if piece == captured_piece:
                    self.pieces[captured_piece.color].remove(piece)
            captured_piece.location = None
        if piece_piece is None:
            raise Game.MoveException("Piece Piece is none.", self)
        piece_piece.location = end
        self.logger.info(f"Turn {self.turn_number}-{self.active_player.value.capitalize()}: {start} to {end}")
        self.finalize_move(start=start, end=end)

    def move_effects(self, start: Location, end: Location | None = None):
        if isinstance(end, str):
            end = Location(end)
        if self.board[end] is None:
            raise Game.MoveException(f"No piece at {end} to apply move effects to, for move {start} {end}", self)
        self.board[end].move_effects(start=start, end=end, game=self)

    def make_compact_move(self, move: str):
        self.logger.debug(f"=== Starting Turn {self.turn_number}-{self.active_player.value.capitalize()} ===")
        self.logger.debug(f"Expanding {self.active_player.value.capitalize()}'s compact move '{move}'")
        parsed_move = self.parse_move(move)
        if move in ("O-O", "O-O-O"):
            self.logger.trace(f"{self.active_player.value.capitalize()} is castling {'kingside' if move == 'O-O' else 'queenside'}")
            self.move(move, None)
        else:
            expanded_move = self.expand_move(parsed_move)
            if expanded_move is None:
                raise Game.MoveException(f"Could not expand {self.active_player.value.capitalize()}'s move: {move}")
            self.logger.trace(f"Parsed {self.active_player.value.capitalize()}'s move {move} into {expanded_move[0]}{' -> ' + expanded_move[1] if expanded_move is not None and len(expanded_move) > 1 else ''}")
            parsed_move['start_square'] = expanded_move[0]
            parsed_move['end_square'] = expanded_move[1]
            try:
                self.move(start=expanded_move[0], end=expanded_move[1])
                if parsed_move['promotion']:

                    self.promote_pawn(expanded_move[1], parsed_move['promotion'])
            except self.MoveException as e:
                self.logger.error(e)
                raise e

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
                'promotion': type_dict[parts['promotion']] if parts['promotion'] else False,
                'capture': True if parts['capture'] else False,
                'check': True if parts['check'] else False,
                'checkmate': True if parts['checkmate'] else False,
                'king_castle': True if parts['kscastle'] else False,
                'queen_castle': True if parts['qscastle'] else False}

    def expand_move(self, parsed_move) -> tuple[str, str | None] | tuple[str, str | None, str]:
        if parsed_move['king_castle'] or parsed_move['queen_castle']:
            return parsed_move, None

        parsed_move = self.determine_start_and_end_squares(parsed_move)
        possibles = self.find_possible_moves(parsed_move)
        self.logger.debug(f"Found {len(possibles)} possible pieces for {self.active_player.value.capitalize()}'s move of {parsed_move['start_square'] if parsed_move['start_square'] is not None else ''}? to {parsed_move['end_square']}: {possibles}")
        if not possibles:
            raise Game.MoveException(f"None of {self.active_player.value.capitalize()}'s {'piece' if parsed_move['start_type'] is None else parsed_move['start_type']}s can move to {parsed_move['end_square']}", self)
        possibles_after_self_check = []
        for p in possibles:
            causes_check = self.does_move_cause_self_check(start=p.location, end=parsed_move['end_square'])
            if causes_check:
                self.logger.debug(f"{self.active_player.value.capitalize()}'s move {parsed_move['move']} would put {self.active_player.value.capitalize()} into check from {causes_check} - eliminating possible move.")
            else:
                possibles_after_self_check.append(p)

        if not possibles_after_self_check:
            raise self.MoveException(f"No moves found for {self.active_player.value.capitalize()}'s {parsed_move['move']} after running self-check detection, but had found {possibles} prior to checking.", self)
        if len(possibles_after_self_check) > 1:
            raise self.MoveException(f"Ambiguous move: {self.active_player.value.capitalize()}'s {parsed_move['move']} could refer to multiple pieces.", self)
        return possibles_after_self_check[0].location, parsed_move['end_square']

    def determine_start_and_end_squares(self, parsed_move):
        if parsed_move['start_type'].__qualname__ == 'King' and parsed_move['start_square'] is None:
            parsed_move['start_square'] = self.find_king_location(self.active_player)
        return parsed_move

    def find_possible_moves(self, parsed_move):
        if parsed_move['capture']:
            return self.find_possible_captures(parsed_move)
        else:
            return self.who_can_move_to(location=parsed_move['end_square'], color_filter=self.active_player, piece_filter=parsed_move['start_type'].__qualname__, file_filter=parsed_move['start_square'][0] if parsed_move['start_square'] else None)

    def find_possible_captures(self, parsed_move):
        if self.enpassants and parsed_move['end_square'] in self.enpassants and parsed_move['start_type'].__qualname__ == 'Pawn' and self.board[parsed_move['end_square']] is None:
            return self.handle_enpassant_possibility(parsed_move)
        elif self.board[parsed_move['end_square']] is None:
            raise self.MoveException(f"Illegal capture: no piece at {parsed_move['end_square']} for {self.active_player.value.capitalize()}'s move {parsed_move['move']}.", self)

        who_can = self.who_can_capture(parsed_move['end_square'], parsed_move['start_type'].__qualname__, parsed_move['start_square'][0] if parsed_move['start_square'] else None, self.active_player)
        return who_can

    def does_move_cause_self_check(self, start, end):
        with self.board.TempMove(self):
            active_player = self.active_player
            self.move(start, end)
            self.active_player = active_player
            is_check = self.is_king_in_check(self.active_player)
            return is_check

    def finalize_move(self, start, end):
        if end is not None:
            self.moves.append((f"{start} {end}", (self.board[start], self.board[end])))
        elif start in ("O-O", "O-O-O"):
            self.moves.append(start)
        self.active_player = Color.BLACK if self.active_player == Color.WHITE else Color.WHITE
        self.check_for_checkmate()
        self.halfmove_counter += 1
        if self.active_player == Color.WHITE:
            self.turn_number += 1

    def promote_pawn(self, location: str, new_type):
        piece = self.board[location]
        if piece is None or not isinstance(piece, Pawn):
            raise self.MoveException(f"{self.active_player.value.capitalize()} you cannot promote piece at {location}, it is not a pawn", self)
        if not ((piece.location[1] == "8" and piece.color == Color.WHITE) or (piece.location[1] == "1" and piece.color == Color.BLACK)):
            raise self.MoveException(f"{self.active_player.value.capitalize()} you can only promote pawns in the end row", self)
        self.board[location] = None
        self.pieces[piece.color].remove(piece)
        new_piece = new_type(piece.color, location)
        self.add_piece(new_piece)

    def handle_enpassant(self, start, end) -> Piece:
        capture_rank = '5' if self.active_player == Color.WHITE else '4'
        square_to_capture = f'{end[0]}{capture_rank}'
        captured_piece = deepcopy(self.board[square_to_capture])
        self.board[square_to_capture] = None
        self._force_move(start, end)
        self.captured_pieces[captured_piece.color].append(captured_piece)
        if self.board[end] is not None:
            self.board[end].move_effects(start, end, self)
        return captured_piece

    def who_can_move_to(self, location, color_filter=None, piece_filter=None, file_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")

        color_filter = color_filter or self.active_player.value
        pieces = []
        self.logger.trace(f"Checking if any of {self.active_player.value.capitalize()}'s {'piece' if piece_filter is None else piece_filter}s can move to {location}")

        for piece in self.pieces[color_filter]:
            if piece_filter is not None and piece.__class__.__name__ != piece_filter:
                continue
            if file_filter is not None and piece.location[0] != file_filter:
                continue

            if piece.can_move_to(location, self):
                logging_string = f"{piece.string()}@{piece.location} matches color filter '{color_filter.value.capitalize()}', matches file filter '{file_filter if file_filter is not None else piece.location[0]}' and can move to {location} - added to list of possibles."
                self.logger.trace(logging_string)
                pieces.append(piece)
        return deepcopy(pieces)

    def castle(self, move: str):
        can_castle = self.can_castle()
        rank = 1 if self.active_player == Color.WHITE else 8
        if move == "O-O":
            if not can_castle[self.active_player]['kingside']:
                raise self.MoveException(f"{self.active_player.value.capitalize()} cannot castle Kingside.", self)
            self._force_move(f"e{rank}", f"g{rank}")
            self._force_move(f"h{rank}", f"f{rank}")
            self.board[f"g{rank}"].has_moved = True
            self.board[f"f{rank}"].has_moved = True
        elif move == "O-O-O":
            if not can_castle[self.active_player]['queenside']:
                raise self.MoveException(f"{self.active_player.value.capitalize()} cannot castle Queenside.", self)
            self._force_move(f"e{rank}", f"c{rank}")
            self._force_move(f"a{rank}", f"d{rank}")
            self.board[f"c{rank}"].has_moved = True
            self.board[f"d{rank}"].has_moved = True

    def can_castle(self) -> dict:
        retval = {Color.WHITE: {'queenside': False, 'kingside': False}, Color.BLACK: {'queenside': False, 'kingside': False}}
        if self.board['e1'] is not None and not self.board['e1'].has_moved and not self.who_can_capture('e1', color_filter=Color.BLACK):
            retval[Color.WHITE]['queenside'] = (self.board['a1'] is not None and not self.board['a1'].has_moved
                                                and self.board['d1'] is None and not self.who_can_capture('d1', color_filter=Color.BLACK)
                                                and self.board['c1'] is None and not self.who_can_capture('c1', color_filter=Color.BLACK))
            retval[Color.WHITE]['kingside'] = (self.board['h1'] is not None and not self.board['h1'].has_moved
                                               and self.board['f1'] is None and not self.who_can_capture('f1', color_filter=Color.BLACK)
                                               and self.board['g1'] is None and not self.who_can_capture('g1', color_filter=Color.BLACK))
        if self.board['e8'] is not None and not self.board['e8'].has_moved and not self.who_can_capture('e8', color_filter=Color.WHITE):
            retval[Color.BLACK]['queenside'] = (self.board['a8'] is not None and not self.board['a8'].has_moved
                                                and self.board['d8'] is None and not self.who_can_capture('d8', color_filter=Color.WHITE)
                                                and self.board['c8'] is None and not self.who_can_capture('c8', color_filter=Color.WHITE))
            retval[Color.BLACK]['kingside'] = (self.board['h8'] is not None and not self.board['h8'].has_moved
                                               and self.board['f8'] is None and not self.who_can_capture('f8', color_filter=Color.WHITE)
                                               and self.board['g8'] is None and not self.who_can_capture('g8', color_filter=Color.WHITE))
        return retval

    def _force_move(self, start: str, end: str):
        if isinstance(start, Location):
            start = str(start.location)
        if isinstance(end, Location):
            end = str(end.location)
        piece_piece = None
        for x in self.pieces[self.active_player]:
            if x.location == start:
                piece_piece = x
        piece_piece.location = end
        piece = self.board[start]
        self.board[start] = None
        self.board[end] = piece

    def handle_enpassant_possibility(self, parsed_move):
        possibles = self.who_can_capture(parsed_move["end_square"], 'Pawn', parsed_move["start_square"][0] if parsed_move["start_square"] else None, self.active_player.value)
        if len(possibles) != 1:
            raise self.MoveException(f"En passant capture ambiguity for move {parsed_move['move']} found {len(possibles)} possiblities {possibles}.", self)
        return possibles

    def find_king_location(self, player_color):
        return next(piece.location for piece in self.pieces[player_color] if isinstance(piece, King))

    def who_can_capture(self, location, piece_filter=None, file_filter=None, color_filter=None):
        if location is None:
            raise ValueError("Location cannot be None")
        pieces = []
        target = self.board[location]
        if color_filter is None:
            if target is None:
                color_filter = self.antiplayer
            else:
                color_filter = target.anticolor()
        for piece in self.pieces[color_filter]:
            if piece_filter is not None and piece.__class__.__name__ != piece_filter:
                continue
            if file_filter is not None and piece.location[0] not in file_filter:
                continue
            if piece.can_take(location, self):
                pieces.append(piece)
        return deepcopy(pieces)

    def get_capture_map(self):
        capture_map = {}
        for square in self.board.iter_square_names():
            possible_captures = self.who_can_capture(square)
            if possible_captures:
                capture_map[square] = possible_captures
        return capture_map

    def is_king_in_check(self, player):
        king = self.get_king(player)
        attackers = self.who_can_capture(king.location, color_filter=self.antiplayer)
        if attackers:
            # self.logger.info(f"King's attackers found: {attackers}")
            x = self.get_king(player)
            return attackers
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
