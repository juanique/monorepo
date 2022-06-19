import os
import sys

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
def sync() -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.sync()
    gg.print_status()


@click.command()
def evolve() -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.evolve()
    gg.print_status()


@click.command()
@click.argument("commit_id")
def update(commit_id: str) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.update(commit_id)
    gg.print_status()


@click.command()
@click.option("-m", "--message")
def commit(message: str) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.commit(message)
    gg.print_status()


@click.command()
@click.option("-s", "--source", default="")
@click.option("-d", "--destination", default="")
@click.option("--continue/--no-continue", "cont_", default=False, is_flag=True)
def rebase(source: str, destination: str, cont_: bool = False) -> None:
    """
    If used with --continue, continues with the current rebase which was
    interrupted by merge conflicts.

    If used with -s/--source and -d/--destination, changes the parent commit of <source>
    to be <destination>.
    """
    if cont_ and (source or destination):
        print("Can't use --continue with --source or --destination")

    gg = GitGud.for_working_dir(os.getcwd())

    if cont_:
        if cont_:
            gg.rebase_continue()
        gg.print_status()
        return

    if not source or not destination:
        print("Both --s/--source and -d/--destination need to be specified")
        sys.exit(1)

    gg.rebase(source, destination)
    gg.print_status()


@click.command()
@click.option("-m", "--message")
def amend(message: str = "") -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.amend(message)
    gg.print_status()


@click.command()
@click.argument("path")
def clone(path: str) -> None:
    # extract the repo name from the URL
    subdir = path.split("/")[-1].split(".")[-2]
    GitGud.clone(path, os.path.join(os.getcwd(), subdir))


@click.command()
def status() -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.print_status()


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
        gg = GitGud.for_working_dir(os.getcwd())
        gg.print_status()
    except Exception as e:  # pylint: disable=broad-except
        handle_failure(e)


def handle_failure(e: Exception) -> None:
    print(f"[bold red]{e}[/bold red]")


cli.add_command(init)
cli.add_command(update)
cli.add_command(test)
cli.add_command(clone)
cli.add_command(status)
cli.add_command(commit)
cli.add_command(amend)
cli.add_command(evolve)
cli.add_command(rebase)
cli.add_command(sync)

if __name__ == "__main__":
    cli()
