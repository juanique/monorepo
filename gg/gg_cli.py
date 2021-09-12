# from gg import GitGud
from gg import GitGud
from git import Repo
import click
import os
from rich import inspect, print


@click.group()
def cli():
    pass


@click.command()
def init():
    click.echo("gg init called")


@click.command()
@click.argument("commit")
def update(commit):
    click.echo(f"gg update {commit} called")


@click.command()
def test():
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
    except Exception as e:
        handle_failure(e)


def handle_failure(e):
    print(f"[bold red]{e}[/bold red]")


cli.add_command(init)
cli.add_command(update)
cli.add_command(test)

if __name__ == "__main__":
    cli()
