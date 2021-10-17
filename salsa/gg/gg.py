from typing import Dict, List, Optional, Callable

import os
import logging
import hashlib
import json

from git import Repo, GitCommandError
from pydantic import BaseModel
from rich import print
from rich.tree import Tree

CONFIGS_ROOT = os.path.expanduser("~/.config/gg")


class InitializationError(Exception):
    pass


class ConfigNotFoundError(Exception):
    pass


class CommitSummary(BaseModel):
    id: str
    hash: str
    is_head: bool = False
    description: str
    children: List["CommitSummary"] = []


class RepoSummary(BaseModel):
    commit_tree: CommitSummary


class GudCommit(BaseModel):
    id: str
    hash: str
    description: str
    needs_evolve: bool = False
    remote: bool = False
    children: List[str] = []
    old_hash: Optional[str] = None

    def get_oneliner(self) -> str:
        return get_oneliner(self.description)


class MergeConflictState(BaseModel):
    current: str
    incoming: str
    files: List[str]


class RepoState(BaseModel):
    head: str
    root: str
    commits: Dict[str, GudCommit] = {}
    merge_conflict_state: Optional[MergeConflictState] = None


def get_branch_name(string: str) -> str:
    return string.split("\n")[0][0:20].lower().replace(" ", "_")


def get_oneliner(string: str) -> str:
    return string.split("\n")[0][0:40]


class GitGud:
    repo: Repo
    state: RepoState

    def __init__(self, repo: Repo, root: GudCommit):
        self.repo = repo
        self.state = RepoState(root=root.id, head=root.id, commits={root.id: root})

    def get_summary(self) -> RepoSummary:
        return RepoSummary(commit_tree=self.get_commit_summary(self.state.root))

    def get_commit_summary(self, commit_id: str) -> CommitSummary:
        commit = self.get_commit(commit_id)
        is_head = commit_id == self.state.head
        summary = CommitSummary(
            id=commit.id, hash=commit.hash, is_head=is_head, description=commit.description
        )
        for child_id in commit.children:
            child_summary = self.get_commit_summary(child_id)
            summary.children.append(child_summary)
        return summary

    @staticmethod
    def load_state_for_directory(directory: str) -> Dict:
        """Load GitGud repo state from the given directory."""

        (_, dirname) = os.path.split(directory)
        hash = hashlib.sha1(bytes(directory, encoding="utf8")).hexdigest()
        filename = f"{dirname}_{hash}"
        config_file = os.path.join(CONFIGS_ROOT, filename)
        if not os.path.exists(config_file):
            raise ConfigNotFoundError(f"Not found {config_file}")

        with open(config_file, encoding="utf-8") as f:
            return json.loads(f.read())

    @staticmethod
    def for_clean_repo(repo: Repo) -> "GitGud":
        commit_msg = "Initial commit"
        commit = repo.index.commit(commit_msg)
        branch_name = get_branch_name(commit_msg)
        root = GudCommit(id=branch_name, hash=commit.hexsha, description=commit_msg)
        return GitGud(repo, root)

    @staticmethod
    def forWorkingDir(working_dir: str) -> "GitGud":
        """Initialize a new GitGud instance from the given directory."""

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

    def traverse(
        self, commit_id: str, func: Callable[[GudCommit], None], skip: bool = False
    ) -> None:
        commit = self.get_commit(commit_id)
        if not skip:
            func(commit)

        for c in commit.children:
            self.traverse(c, func)

    def serialize(self) -> Dict:
        return {
            "working_dir": self.repo.working_dir,
        }

    def add_changes_to_index(self) -> None:
        """Equivalent of git add ."""

        index = self.repo.index
        for (path, stage), entry in index.entries.items():
            logging.info("file in index: path: %s, stage: %s, entry: %s", path, stage, entry)

        for item in self.repo.index.diff(None):
            logging.info("Adding modified file: %s", item.a_path)
            index.add(item.a_path)

        for untracked in self.repo.untracked_files:
            logging.info("Adding untracked file: %s", untracked)
            index.add(untracked)

    def commit(self, commit_msg: str, all: bool = True) -> GudCommit:
        """Create a new commit that includes all local changes."""

        logging.info("Creating new commit: %s", get_oneliner(commit_msg))
        branch_name = get_branch_name(commit_msg)

        if self.head():
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()

        if all:
            self.add_changes_to_index()

        commit = self.repo.index.commit(commit_msg)
        gud_commit = GudCommit(id=branch_name, hash=commit.hexsha, description=commit_msg)

        if self.head():
            self.head().children.append(gud_commit.id)

        self.state.head = gud_commit.id
        logging.info("Created commit (%s): %s", gud_commit.id, get_oneliner(commit_msg))
        self.state.commits[gud_commit.id] = gud_commit

        return gud_commit

    def amend(self) -> None:
        """Amend the commit with current changes, updates hash.

        All descendants of this commit are marked as needing evolve.
        """

        if not self.head():
            return

        self.add_changes_to_index()
        self.repo.git.commit("--amend", "--no-edit")

        new_hash = self.repo.head.commit.hexsha
        self.head().old_hash, self.head().hash = self.head().hash, new_hash

        def f(c: GudCommit) -> None:
            c.needs_evolve = True

        self.traverse(self.head().id, f, skip=True)

    def merge_conflict_begin(
        self, current: GudCommit, incoming: GudCommit, files: List[str]
    ) -> None:
        self.state.merge_conflict_state = MergeConflictState(
            current=current.id, incoming=incoming.id, files=files
        )

    def head(self) -> GudCommit:
        return self.get_commit(self.state.head)

    def root(self) -> GudCommit:
        return self.get_commit(self.state.root)

    def evolve(self) -> None:
        """Propagate changes of amended commit onto all descendants."""

        if not self.head().children:
            print("No children to evolve.")
            return

        if not self.get_commit(self.head().children[0]).needs_evolve:
            print("No need to evolve")
            return

        if len(self.head().children) > 1:
            print("TODO - Not supported for multiple children")
            return

        child = self.get_commit(self.head().children[0])
        try:
            self.repo.git.rebase("--onto", self.head().hash, self.head().old_hash, child.id)
        except GitCommandError as e:
            lines = e.stdout.split("\n")
            files = []
            for l in lines:
                if "CONFLICT" in l:
                    files.append(l.split(" ")[-1])

            if not files:
                raise Exception(f"Unknown error: {e.stdout}") from e

            self.merge_conflict_begin(self.head(), child, files)
            return

        self.update(child.id)

    def update(self, commit_id: str) -> None:
        self.repo.git.checkout(commit_id)
        self.state.head = commit_id

    def rebase_continue(self) -> None:
        """Accept the current changes and continue rebase."""

        if not self.state.merge_conflict_state:
            raise ValueError("No rebase in progress")
        for file in self.state.merge_conflict_state.files:
            self.repo.git.add(file)

        self.repo.git.rebase("--continue")
        if self.state.merge_conflict_state:
            self.get_commit(self.state.merge_conflict_state.incoming).needs_evolve = False
            self.update(self.state.merge_conflict_state.incoming)
            self.state.merge_conflict_state = None

    def get_commit(self, id: str) -> GudCommit:
        if id not in self.state.commits:
            raise Exception(f"Commit not found: {id}")
        return self.state.commits[id]

    def print_status(self) -> None:
        """Print the state of the local branches."""

        if self.state.merge_conflict_state:
            print("[bold red]Rebase in progress[/bold red]: stopped due to merge conflict.")
        print("")
        tree = self.get_tree()
        print(tree)
        print("")
        if self.state.merge_conflict_state:
            print("Files with merge conflict:")

            for f in self.state.merge_conflict_state.files:
                print(f"  - [bold red]{f}[/bold red]")

            print("")
            print("Resolve conflicts and run:")
            print(" [bold]gg rebase --continue[/bold]")
            print("")
            print("To abort run:")
            print(" [bold]gg rebase --abort[/bold]")

    def get_tree(self, commit: GudCommit = None, tree: Tree = None) -> Tree:
        """Return a tree representation of the local gitgud state for printing."""

        commit = commit or self.root()
        color = "green" if commit == self.head() else "magenta"

        needs_evolve = ""
        if commit.needs_evolve and not self.state.merge_conflict_state:
            needs_evolve = "*"

        conflict = ""
        if self.state.merge_conflict_state:
            conflict_type = ""
            if commit.id == self.state.merge_conflict_state.current:
                conflict_type = "current"
            if commit.id == self.state.merge_conflict_state.incoming:
                conflict_type = "incoming"
            if self.state.merge_conflict_state and conflict_type:
                conflict = f" [bold red]({conflict_type})[/bold red]"

        remote = ""
        if commit.remote:
            remote = " [bold yellow](Remote Head)[/bold yellow]"

        line = f"[bold {color}]{commit.hash}[/bold {color}]"
        line += f"{needs_evolve}{conflict}{remote}: {commit.get_oneliner()}"

        if not tree:
            branch = Tree(line)
        else:
            branch = tree.add(line)

        for child_id in commit.children:
            self.get_tree(self.get_commit(child_id), branch)

        return branch