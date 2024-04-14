from rich.console import Console
from rich.table import Table
from rich.text import Text
from pgnload import PgnLoader


def read_games(file_path):
    with open(file_path, 'r') as file:
        game = []
        state = 0  # 0 = Capturing Tags, #1 = Encountered first blank line, #2 = Encountered Move line, #3 = Encountered second blank line
        for line in file:
            if line.strip().startswith('['):
                if state != 0:
                    raise Exception(f"Should not encounter a line starting with [ when outside of state 0, but in state {state}")
                game.append(line.strip())
                continue
            if line.strip() == '':
                if state == 0:
                    state = 1
                    game.append('')
                elif state == 2:
                    state = 0
                    game.append('')
                    yield '\n'.join(game)
                    game = []
                else:
                    raise Exception(f"Should not encounter a blank line outside of state 0 or 2, but in state {state}")
            else:
                if state == 1:
                    state = 2
                    game.append(line.strip())


def run_games(filename, stop_on_fail=False, detail=False):
    table = Table(title=filename, show_lines=True)

    table.add_column("Game Name", justify="center", style="cyan", no_wrap=True)
    table.add_column("Result", justify="center", style="green")
    num_pass = 0
    num_fail = 0
    failed_games = []
    for game in read_games(filename):
        pgnloader = PgnLoader()
        pgnloader.load_str(game)
        result = pgnloader.play_game()
        if result[0] in (None, 'draw', 'end'):
            table.add_row(pgnloader.vs_str, "[bold green]PASS[/bold green]")
            num_pass += 1
        else:
            cell_text = Text("FAIL\n", style="bold red")
            cell_text.append_text(Text(f"Turn #{result[0].args[0].turn_number}\n", style='yellow'))
            cell_text.append_text(Text(result[0].args[1], style='cyan'))
            cell_text.append_text(Text("\n", style='bright white'))
            cell_text.append_text(result[0].args[0].create_board_text())
            cell_text.append_text(Text(f"\n{pgnloader.tags['site']}", style='bright white'))
            table.add_row(pgnloader.vs_str, cell_text)
            num_fail += 1
            failed_games.append(game)
            if stop_on_fail:
                break

    table.title = f"{filename}\n{(num_pass / (num_pass + num_fail)) * 100:.2f}%"
    console = Console()
    console.print(table)
    if filename.find("failed") == -1:
        filename = f"{filename[:-4]}-failed.pgn"
    with open(filename, "w") as outfile:
        for game in failed_games:
            outfile.write(game + '\n')


run_games("pgn_files/lichess_2013-01-example.pgn")
