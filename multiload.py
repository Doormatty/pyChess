import concurrent.futures

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


def run_games(filename, stop_on_fail=False, loglevel="INFO"):
    table = Table(title=filename, show_lines=True)

    table.add_column("Game Name", justify="center", style="cyan", no_wrap=True)
    table.add_column("Result", justify="center", style="green")
    num_pass = 0
    num_fail = 0
    failed_games = []
    import atexit

    atexit.register(_save_failed_games, failed_games, filename)
    for game in read_games(filename):
        pgnloader = PgnLoader(loglevel=loglevel)
        pgnloader.load_str(game)
        try:
            result = pgnloader.play_game()
        except Exception as e:
            table.add_row(pgnloader.vs_str, e.args[0])
        else:
            if result is not None and result[0] in (None, 'draw', 'end'):
                table.add_row(pgnloader.vs_str, "[bold green]PASS[/bold green]")
                num_pass += 1
            else:
                cell_text = Text("FAIL\n", style="bold red")
                if result is not None:
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
    try:
        table.title = f"{filename}\n{(num_pass / (num_pass + num_fail)) * 100:.2f}%"
    except ZeroDivisionError:
        table.title = f"{filename}\n0%"
    console = Console()
    console.print(table)
    if filename.find("failed") == -1:
        filename = f"{filename[:-4]}-failed.pgn"
    with open(filename, "w") as outfile:
        for game in failed_games:
            outfile.write(game + '\n')


def _rungame(gamestring, loglevel="INFO"):
    pgnloader = PgnLoader(loglevel=loglevel, game_string=gamestring)

    try:
        result = pgnloader.play_game()
    except Exception as e:
        return e
    if result is not None and result[0] in (None, 'draw', 'end'):
        return result, pgnloader
    else:
        return None


def _save_failed_games(games, filename):
    if filename.find("failed") == -1:
        filename = f"{filename[:-4]}-failed.pgn"
    with open(filename, "w") as outfile:
        for game in games:
            outfile.write(game + '\n')


def multi_run_games(filename, loglevel="INFO"):
    table = Table(title=filename, show_lines=True)

    table.add_column("Game Name", justify="center", style="cyan", no_wrap=True)
    table.add_column("Result", justify="center", style="green")
    num_pass = 0
    num_fail = 0
    failed_games = []
    games = {}
    import atexit

    atexit.register(_save_failed_games, games, filename)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for game_num, game in enumerate(read_games(filename)):
            games[game_num] = executor.submit(_rungame, game, loglevel=loglevel)

    for future in concurrent.futures.as_completed(games):
        try:
            result = future.result()
        except Exception as e:
            result = None
        if result is not None:
            if len(result) == 2:
                pgnloader = result[1]
                result = result[0]
                if result is not None and result[0] in (None, 'draw', 'end'):
                    table.add_row(pgnloader.vs_str, "[bold green]PASS[/bold green]")
                    num_pass += 1
                else:
                    cell_text = Text("FAIL\n", style="bold red")
                    if result is not None:
                        cell_text.append_text(Text(f"Turn #{result[0].args[0].turn_number}\n", style='yellow'))
                        cell_text.append_text(Text(result[0].args[1], style='cyan'))
                        cell_text.append_text(Text("\n", style='bright white'))
                        cell_text.append_text(result[0].args[0].create_board_text())
                    cell_text.append_text(Text(f"\n{pgnloader.tags['site']}", style='bright white'))
                    table.add_row(pgnloader.vs_str, cell_text)
                    num_fail += 1
                    failed_games.append(game)
        else:
            num_fail += 1
        if num_pass + num_fail % 100 == 0:
            print(f'{num_pass + num_fail}')

    table.title = f"{filename}\n{(num_pass / (num_pass + num_fail)) * 100:.2f}%"
    console = Console()
    console.print(table)


run_games("pgn_files/lichess_2013-01-failed.pgn", loglevel="ERROR")
