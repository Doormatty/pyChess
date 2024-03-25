from rich import print
from rich.console import Console
from board import Board

console = Console()

board=Board()
print(board.export_to_fen())
