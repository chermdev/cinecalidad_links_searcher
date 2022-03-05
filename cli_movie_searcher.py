from rich import box
from rich.table import Table
from rich.console import Console
from configparser import ConfigParser
from src.exceptions import *
from __init__ import search_movie
import os
import sys
import platform


config = ConfigParser()
config.read('config.ini')

console = Console()


def _clear_console() -> None:
    os.system('cls') if platform.system() == 'Windows' else os.system('clear')
    _print_header()


def _print_header() -> None:
    console.print(
        f"Movie Searcher in {config['config']['host']}", justify="center", style="bold green")


if __name__ == '__main__':

    movie_found = None
    movie_title = ""

    while movie_found != True:
        _clear_console()

        if movie_found == False:
            console.print(f"Movie [yellow on grey0]'{movie_title}'[/] not found.",
                          style="bright_white on grey0")

        movie_title = console.input("[yellow](exit with 'q')[/] Search: ")

        if movie_title == "q":
            sys.exit()

        try:
            movies_found = search_movie(movie_title)
        except MovieNotFound:
            movie_found = False
        else:
            movie_found = True

    while True:
        table = Table(title="Movies Found", box=box.SQUARE, show_lines=True)
        table.add_column("No.", style="bright_white", vertical="middle")
        table.add_column("Info", style="bright_white",
                         overflow="fold", vertical="middle")
        table.add_column("Description", style="bright_white",
                         vertical="middle")
        for n, movie in enumerate(movies_found, start=1):
            coincidence = "{:.2f}%".format(movie.coincidence*100.00)
            movie_info = "\n".join(["[bright_green]"+movie.title+"[/]",
                                    movie.duration,
                                    ",".join(movie.categories),
                                    "[bright_cyan]"+movie.url+"[/]"])
            table.add_row(f"[[bright_green]#{n}[/]]",
                          movie_info, movie.description, )
        console.print(table)
        if len(movies_found) > 1:
            ans = console.input(
                "[yellow](exit with 'q')[/] Select a movie Number: [bright_green]#[/]")
            if ans == 'q':
                sys.exit()
        else:
            ans = 1
        movie_selected = movies_found[int(ans)-1]
        _clear_console()
        table = Table(title=f"Movie [[bright_green]#{ans}[/]] Selected",
                      box=box.SQUARE, title_justify="left")
        table.add_column("No.", style="bright_white", vertical="middle")
        table.add_column("Info", style="bright_white",
                         overflow="fold", vertical="middle")
        table.add_column("Description", style="bright_white",
                         vertical="middle")
        coincidence = "{:.2f}%".format(movie_selected.coincidence*100.00)
        movie_info = "\n".join(["[bright_green]"+movie_selected.title+"[/]",
                                movie_selected.duration,
                                ",".join(movie_selected.categories),
                                "[bright_cyan]"+movie_selected.url+"[/]"])
        table.add_row(f"[[bright_green]#{ans}[/]]",
                      movie_info, movie_selected.description)
        console.print(table)
        print("\n")
        console.print("Loading Download Options... ", end="\r")
        table = Table(title="Download Options                 ",
                      box=box.SQUARE, title_justify="left", expand=False, show_lines=True)
        table.add_column("No.", style="bright_white", vertical="middle")
        table.add_column("Server", style="bright_white", vertical="middle")
        table.add_column("Link", style="bright_cyan",
                         overflow="fold", vertical="middle")
        download_severs = movie_selected.download_options
        for n, download_opt in enumerate(download_severs, start=1):
            table.add_row(f"[[bright_cyan]{n}[/]]",
                          download_opt.name, download_opt.link)
        console.print(table)
        input('Press ENTER to exit')
        sys.exit()
