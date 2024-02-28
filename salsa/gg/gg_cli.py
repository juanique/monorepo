import os
import sys

from git import Repo
from rich import inspect, print
import click

from salsa.gg.gg import GitGud


# cambios
@click.group()
def cli() -> None:
    pass


@click.command()
def init() -> None:
    click.echo("gg init called")


@click.command()
def debug() -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    print(gg.state.dict())


@click.command()
@click.option("--all/--no-all", "all_", default=False, is_flag=True)
def upload(all_: bool) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.upload(all_commits=all_)
    gg.print_status()


@click.command()
@click.option("--all/--no-all", "all_", default=False, is_flag=True)
def sync(all_: bool) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.sync(all=all_)
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
@click.argument("commit_id")
def drop(commit_id: str) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.drop_commit(commit_id)
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
def squash(source: str, destination: str) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.squash(source_id=source, dest_id=destination)


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
def get_config() -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    print(gg.get_config())


@click.command()
def version() -> None:
    print("gg-version-alpha-2")


@click.command()
@click.option("-k", "--key")
@click.option("-v", "--value")
def set_config(key: str, value: str) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    config = gg.get_config()
    setattr(config, key, value)
    gg.set_config(config)


@click.command()
@click.argument("path")
def clone(path: str) -> None:
    # extract the repo name from the URL
    subdir = path.split("/")[-1].split(".")[-2]
    GitGud.clone(path, os.path.join(os.getcwd(), subdir))


@click.command()
@click.option("--full/--no-full", default=False, is_flag=True)
def status(full: bool = False) -> None:
    gg = GitGud.for_working_dir(os.getcwd())
    gg.print_status(full=full)


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
cli.add_command(upload)
cli.add_command(debug)
cli.add_command(drop)
cli.add_command(get_config)
cli.add_command(set_config)
cli.add_command(version)
cli.add_command(squash)

if __name__ == "__main__":
    cli()
