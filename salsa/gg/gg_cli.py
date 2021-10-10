import os

from git import Repo
from rich import inspect, print
import click

from salsa.gg.gg import GitGud


@click.group()
def cli() -> None:
    pass


@click.command()
def init() -> None:
    click.echo("gg init called")


@click.command()
@click.argument("commit")
def update(commit: str) -> None:
    click.echo(f"gg update {commit} called")


@click.command()
def test() -> None:
    """Just a test command for development."""

    try:
        repo = Repo(os.getcwd())
        inspect(repo)
        inspect(repo.head)
        inspect(repo.head.ref)
        inspect(repo.head.commit)
        inspect(repo.active_branch)
        inspect(repo.active_branch.tracking_branch())
        inspect(repo.active_branch.commit)
        gg = GitGud.forWorkingDir(os.getcwd())
        gg.print_status()
    except Exception as e:  # pylint: disable=broad-except
        handle_failure(e)


def handle_failure(e: Exception) -> None:
    print(f"[bold red]{e}[/bold red]")


cli.add_command(init)
cli.add_command(update)
cli.add_command(test)

if __name__ == "__main__":
    cli()
