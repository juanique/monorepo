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


class InvalidOperationForRemote(Exception):
    pass


class DirtyState(BaseModel):
    """Exposes data of the diff between current state of the filesystem and
    locally or remotely commited state."""

    untracked_files: List[str] = []
    modified_files: List[str] = []


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
    repo_dir: str
    head: str
    root: str
    commits: Dict[str, GudCommit] = {}
    merge_conflict_state: Optional[MergeConflictState] = None


def get_branch_name(string: str) -> str:
    return string.split("\n")[0][0:20].lower().replace(" ", "_").replace(".", "")


def get_oneliner(string: str) -> str:
    return string.split("\n")[0][0:40]


class GitGud:
    repo: Repo
    state: RepoState

    def __init__(self, repo: Repo, state: RepoState):
        self.repo = repo
        self.state = state

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
    def state_filename(directory: str) -> str:
        (_, dirname) = os.path.split(directory)
        hash = hashlib.sha1(bytes(directory, encoding="utf8")).hexdigest()
        filename = f"{dirname}_{hash}"
        return os.path.join(CONFIGS_ROOT, filename)

    def save_state(self) -> None:
        os.makedirs(CONFIGS_ROOT, exist_ok=True)
        state_filename = GitGud.state_filename(self.state.repo_dir)
        with open(state_filename, "w", encoding="utf-8") as out_file:
            json.dump(self.state.dict(), out_file, sort_keys=True, indent=4, ensure_ascii=False)

    @staticmethod
    def clone(remote_repo_path: str, local_repo_path: str) -> "GitGud":
        """Clone an external repo into the given path."""
        repo = Repo.clone_from(remote_repo_path, local_repo_path)

        root = GudCommit(
            id=repo.head.ref.name,
            hash=repo.head.commit.hexsha,
            description=repo.head.commit.message,
            remote=True,
        )
        state = RepoState(
            repo_dir=local_repo_path, root=root.id, head=root.id, commits={root.id: root}
        )
        gg = GitGud(repo, state)
        gg.save_state()
        return gg

    @staticmethod
    def load_state_for_directory(directory: str) -> RepoState:
        """Load GitGud repo state from the given directory."""

        state_file = GitGud.state_filename(directory)
        if not os.path.exists(state_file):
            raise ConfigNotFoundError(f"No GitGud state for {directory}.")

        with open(state_file, encoding="utf-8") as f:
            obj = json.loads(f.read())
            return RepoState(**obj)

    @staticmethod
    def for_clean_repo(repo: Repo) -> "GitGud":
        commit_msg = "Initial commit"
        commit = repo.index.commit(commit_msg)
        branch_name = get_branch_name(commit_msg)
        root = GudCommit(id=branch_name, hash=commit.hexsha, description=commit_msg)
        state = RepoState(
            repo_dir=repo.working_tree_dir, root=root.id, head=root.id, commits={root.id: root}
        )
        return GitGud(repo, state)

    @staticmethod
    def for_working_dir(working_dir: str) -> "GitGud":
        """Resume a GitGud instance for a previously cloned directory."""

        repo_state = GitGud.load_state_for_directory(working_dir)
        repo = Repo(working_dir)
        return GitGud(repo, repo_state)

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

        self.save_state()
        return gud_commit

    def amend(self) -> None:
        """Amend the commit with current changes, updates hash.

        All descendants of this commit are marked as needing evolve.
        """

        if not self.head():
            return

        if self.head().remote:
            raise InvalidOperationForRemote("Cannot amend remote commits.")

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
        self.save_state()

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
        print("")
        dirty_state = self.get_dirty_state()

        if dirty_state.modified_files:
            print("Modified files:")
            for filename in dirty_state.modified_files:
                print(f" [bold red]{filename}[/bold red]")
            print("")

        if dirty_state.untracked_files:
            print("Untracked files:")
            for filename in dirty_state.untracked_files:
                print(f" [bold red]{filename}[/bold red]")
            print("")

        if self.state.merge_conflict_state:
            print("[bold red]Rebase in progress[/bold red]: stopped due to merge conflict.")
            print("")
        tree = self.get_tree()
        print(tree)
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
        print("")

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

        line = f"[bold {color}]{commit.id}[/bold {color}]"
        line += f"{needs_evolve}{conflict}{remote}: {commit.get_oneliner()}"

        if not tree:
            branch = Tree(line)
        else:
            branch = tree.add(line)

        for child_id in commit.children:
            self.get_tree(self.get_commit(child_id), branch)

        return branch

    def get_dirty_state(self) -> DirtyState:
        state = DirtyState()
        for item in self.repo.index.diff(None):
            state.modified_files.append(item.a_path)

        for untracked in self.repo.untracked_files:
            state.untracked_files.append(untracked)

        return state
