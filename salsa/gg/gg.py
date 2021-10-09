from typing import Dict, List, Optional, Callable, Any

import os
import logging
import hashlib
import json

from git import Repo, GitCommandError
from rich import print
from rich.tree import Tree

CONFIGS_ROOT = os.path.expanduser("~/.config/gg")


class InitializationError(Exception):
    pass


class ConfigNotFoundError(Exception):
    pass


class GudCommit:
    id: str
    hash: str
    description: str
    parent: Optional["GudCommit"]
    needs_evolve: bool
    remote: bool
    children: List["GudCommit"]
    old_hash: Optional[str]

    def __init__(self, id: str, hash: str, description: str = "", remote: bool = False):
        self.id = id
        self.hash = hash
        self.description = description
        self.parent = None
        self.needs_evolve = False
        self.remote = remote
        self.children = []

    def add_child(self, commit: "GudCommit") -> None:
        self.children.append(commit)
        commit.parent = self

    def get_oneliner(self) -> str:
        return get_oneliner(self.description)

    def __eq__(self, other: Any) -> bool:
        if type(other) != type(self):
            return False
        return self.id == other.id

    def __neq__(self, other: Any) -> bool:
        return self.id != other.id


class MergeConflictState:
    current: GudCommit
    incoming: GudCommit
    files: List[str]

    def __init__(self, current: GudCommit, incoming: GudCommit, files: List[str]):
        self.current = current
        self.incoming = incoming
        self.files = files


def get_branch_name(string: str) -> str:
    return string.split("\n")[0][0:20].lower().replace(" ", "_")


def get_oneliner(string: str) -> str:
    return string.split("\n")[0][0:40]


def traverse(commit: GudCommit, func: Callable[[GudCommit], None], skip: bool = False) -> None:
    if not skip:
        func(commit)

    for c in commit.children:
        traverse(c, func)


class GitGud:
    repo: Repo
    head: Optional[GudCommit]
    commits: Dict[str, GudCommit]
    merge_conflict_state: Optional[MergeConflictState]
    root: GudCommit

    def __init__(self, repo: Repo, root: Optional[GudCommit] = None):
        self.repo = repo
        self.head = None
        self.commits = {}
        self.merge_conflict_state = None
        self.root = root or self.commit("Initial commit", all=False)

    @staticmethod
    def load_state_for_directory(directory: str) -> Dict:
        (_, dirname) = os.path.split(directory)
        hash = hashlib.sha1(bytes(directory, encoding="utf8")).hexdigest()
        filename = f"{dirname}_{hash}"
        config_file = os.path.join(CONFIGS_ROOT, filename)
        if not os.path.exists(config_file):
            raise ConfigNotFoundError(f"Not found {config_file}")

        with open(config_file) as f:
            return json.loads(f.read())

    @staticmethod
    def forWorkingDir(working_dir: str) -> "GitGud":
        repo = Repo(working_dir)
        branch = repo.active_branch

        # repo_state = GitGud.load_state_for_directory(working_dir)

        up_to_date = True
        if branch.commit.hexsha != branch.tracking_branch().commit.hexsha:
            up_to_date = False

        if not up_to_date or repo.is_dirty():
            raise InitializationError(
                "Cannnot initialize gg repo on top of local changes, sync to " "remote head first."
            )

        root = GudCommit(
            id=repo.head.ref.name,
            hash=repo.head.commit.hexsha,
            description=repo.head.commit.message,
            remote=True,
        )
        return GitGud(repo=repo, root=root)

    def serialize(self) -> Dict:
        return {
            "working_dir": self.repo.working_dir,
        }

    def add_changes_to_index(self) -> None:
        index = self.repo.index
        for (path, stage), entry in index.entries.items():
            logging.info(f"file in index: path: {path}, stage: {stage}, entry: {entry}")

        for item in self.repo.index.diff(None):
            logging.info("Adding modified file: %s", item.a_path)
            index.add(item.a_path)

        for untracked in self.repo.untracked_files:
            logging.info("Adding untracked file: %s", untracked)
            index.add(untracked)

    def commit(self, commit_msg: str, all: bool = True) -> GudCommit:
        logging.info("Creating new commit: %s", get_oneliner(commit_msg))
        branch_name = get_branch_name(commit_msg)

        if self.head:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()

        if all:
            self.add_changes_to_index()

        commit = self.repo.index.commit(commit_msg)
        gud_commit = GudCommit(id=branch_name, hash=commit.hexsha, description=commit_msg)

        if self.head:
            self.head.add_child(gud_commit)

        self.head = gud_commit
        logging.info("Created commit (%s): %s", gud_commit.id, get_oneliner(commit_msg))
        self.commits[gud_commit.id] = gud_commit
        return gud_commit

    def amend(self) -> None:
        if not self.head:
            return

        self.add_changes_to_index()
        self.repo.git.commit("--amend", "--no-edit")

        new_hash = self.repo.head.commit.hexsha
        self.head.old_hash, self.head.hash = self.head.hash, new_hash

        def f(c: GudCommit) -> None:
            c.needs_evolve = True

        traverse(self.head, f, skip=True)

    def merge_conflict_begin(
        self, current: GudCommit, incoming: GudCommit, files: List[str]
    ) -> None:
        self.merge_conflict_state = MergeConflictState(current, incoming, files)

    def evolve(self) -> None:
        if not self.head:
            return

        if not self.head.children:
            print("No children to evolve.")
            return

        if not self.head.children[0].needs_evolve:
            print("No need to evolve")
            return

        if len(self.head.children) > 1:
            print("TODO - Not supported for multiple children")

        child = self.head.children[0]
        try:
            self.repo.git.rebase("--onto", self.head.hash, self.head.old_hash, child.id)
        except GitCommandError as e:
            lines = e.stdout.split("\n")
            files = []
            for l in lines:
                if "CONFLICT" in l:
                    files.append(l.split(" ")[-1])

            if not files:
                raise Exception("Unknown error: %s" % e.stdout)

            self.merge_conflict_begin(self.head, child, files)
            return

        self.update(child.id)

    def update(self, commit_id: str) -> None:
        self.repo.git.checkout(commit_id)
        self.head = self.commits[commit_id]

    def rebase_continue(self) -> None:
        if not self.merge_conflict_state:
            raise ValueError("No rebase in progress")
        for file in self.merge_conflict_state.files:
            self.repo.git.add(file)

        self.repo.git.rebase("--continue")
        if self.merge_conflict_state:
            self.merge_conflict_state.incoming.needs_evolve = False
            self.update(self.merge_conflict_state.incoming.id)
            self.merge_conflict_state = None

    def print_status(self) -> None:
        if self.merge_conflict_state:
            print(f"[bold red]Rebase in progress[/bold red]: stopped due to merge conflict.")
        print("")
        tree = self.get_tree()
        print(tree)
        print("")
        if self.merge_conflict_state:
            print("Files with merge conflict:")

            for f in self.merge_conflict_state.files:
                print(f"  - [bold red]{f}[/bold red]")

            print("")
            print("Resolve conflicts and run:")
            print(" [bold]gg rebase --continue[/bold]")
            print("")
            print("To abort run:")
            print(" [bold]gg rebase --abort[/bold]")

    def get_tree(self, commit: GudCommit = None, tree: Tree = None) -> Tree:
        commit = commit or self.root
        color = "green" if commit == self.head else "magenta"

        needs_evolve = ""
        if commit.needs_evolve and not self.merge_conflict_state:
            needs_evolve = "*"

        conflict = ""
        if self.merge_conflict_state:
            conflict_type = ""
            if commit.id == self.merge_conflict_state.current.id:
                conflict_type = "current"
            if commit.id == self.merge_conflict_state.incoming.id:
                conflict_type = "incoming"
            if self.merge_conflict_state and conflict_type:
                conflict = f" [bold red]({conflict_type})[/bold red]"

        remote = ""
        if commit.remote:
            remote = " [bold yellow](Remote Head)[/bold yellow]"

        line = f"[bold {color}]{commit.hash}[/bold {color}]{needs_evolve}{conflict}{remote}: {commit.get_oneliner()}"
        if not tree:
            branch = Tree(line)
        else:
            branch = tree.add(line)

        for child in commit.children:
            self.get_tree(child, branch)

        return branch
