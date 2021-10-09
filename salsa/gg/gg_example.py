import os
import shutil
from git import Repo
from gg.gg import GitGud, GudCommit

REPO_DIR = "/tmp/repo_dir"


def append(filename: str, contents: str) -> None:
    with open(os.path.join(REPO_DIR, filename), "a") as file:
        file.write(contents)
        file.write("\n")


def set_file_contents(filename: str, contents: str) -> None:
    with open(os.path.join(REPO_DIR, filename), "w") as file:
        file.write(contents)
        file.write("\n")


if os.path.isdir(REPO_DIR):
    shutil.rmtree(REPO_DIR)

os.mkdir(REPO_DIR)
repo = Repo.init(REPO_DIR)
gg = GitGud(repo, {})

append("file1.txt", "testing1")
c1 = gg.commit("My first commit")
append("file1.txt", "testing2")
c2 = gg.commit("My second commit")

gg.update(c1.id)
append("file1.txt", "testing3")

gg.amend()
gg.evolve()

set_file_contents("file1.txt", "testing1\ntesting2\ntesting3")
gg.rebase_continue()

gg.print_status()
