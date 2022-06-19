from enum import Enum
from typing import Dict, List, Optional, Callable

import os
import logging
import hashlib
import json

from git import Repo, GitCommandError
from pydantic import BaseModel
from rich import print
from rich.tree import Tree

from salsa.os.environ_ctx import modified_environ

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


class Snapshot(BaseModel):
    hash: str
    description: str


class GudCommit(BaseModel):
    id: str
    hash: str
    description: str
    needs_evolve: bool = False
    remote: bool = False
    children: List[str] = []
    old_hash: Optional[str]
    parent_hash: Optional[str]

    history_branch: Optional[str]
    snapshots: List[Snapshot] = []

    def get_oneliner(self) -> str:
        return get_oneliner(self.description)

    def get_metadata_for_snapshot(self) -> Snapshot:
        return Snapshot(hash=self.hash, description=self.description)


class MergeConflictState(BaseModel):
    current: str
    incoming: str
    files: List[str]


class OperationType(str, Enum):
    EVOLVE = "EVOLVE"


class EvolveOperation(BaseModel):
    base_commit_id: str
    target_commit_id: str


class PendingOperation(BaseModel):
    type: OperationType
    evolve_op: EvolveOperation


class RepoState(BaseModel):
    repo_dir: str
    head: str
    root: str
    commits: Dict[str, GudCommit] = {}
    merge_conflict_state: Optional[MergeConflictState] = None
    pending_operations: List[PendingOperation] = []
    master_branch: str = "master"

    class Config:
        use_enum_values = True


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
    def get_remote_commit(repo: Repo) -> GudCommit:
        master_commit_id = f"master@{repo.head.commit.hexsha[0:8]}"
        new_branch = repo.create_head(master_commit_id)
        new_branch.checkout()

        return GudCommit(
            id=master_commit_id,
            hash=repo.head.commit.hexsha,
            description=repo.head.commit.message.strip(),
            remote=True,
        )

    @staticmethod
    def clone(remote_repo_path: str, local_repo_path: str) -> "GitGud":
        """Clone an external repo into the given path."""
        repo = Repo.clone_from(remote_repo_path, local_repo_path)
        root = GitGud.get_remote_commit(repo)

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

    def sync(self) -> None:
        if self.head().remote:
            self.pull_remote()
            return
        raise ValueError("Not implemented for non-remote commits.")

    def pull_remote(self) -> None:
        """Pulls the latest commit from remote master and adds it as a child of
        the most recent remote commit."""

        # Get the newest remote commit
        newest_remote = None
        for commit in self.state.commits.values():
            if commit.remote:
                if not newest_remote:
                    newest_remote = commit
                    continue

                revcount = int(
                    self.repo.rev_list("--count", f"{newest_remote.hash}..{commit.hash}")
                )
                if revcount > 0:
                    newest_remote = commit
                    continue

        if not newest_remote:
            raise ValueError("No remote commits")

        logging.info("Starting of more recent remote commit %s", newest_remote.id)

        self.repo.git.checkout(self.state.master_branch)
        self.repo.git.pull("--rebase", "origin", self.state.master_branch)
        pulled_commit = GitGud.get_remote_commit(self.repo)

        if newest_remote.children:
            newest_remote.children.insert(0, pulled_commit.id)
        else:
            # We only keep one remote commit with no children.
            if self.state.root == newest_remote.id:
                self.state.root = pulled_commit.id

            self.state.commits.pop(newest_remote.id)

        self.state.commits[pulled_commit.id] = pulled_commit
        self.update(pulled_commit.id)

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

        for item in self.repo.index.diff(None):
            if item.change_type == "D":
                index.remove(item.a_path)
                continue
            index.add(item.a_path)

        for untracked in self.repo.untracked_files:
            logging.info("Adding untracked file: %s", untracked)
            index.add(untracked)

    def commit(self, commit_msg: str, all: bool = True) -> GudCommit:
        """Create a new commit that includes all local changes."""

        if self.state.merge_conflict_state:
            raise ValueError("Cannot commit during merge conflict.")

        logging.info("Creating new commit: %s", get_oneliner(commit_msg))
        branch_name = get_branch_name(commit_msg)
        history_branch_name = f"history_{branch_name}"

        if self.head():
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()

        if all:
            self.add_changes_to_index()

        commit = self.repo.index.commit(commit_msg)
        gud_commit = GudCommit(
            id=branch_name,
            history_branch=history_branch_name,
            hash=commit.hexsha,
            description=commit_msg,
            parent_hash=self.head().hash,
        )
        gud_commit.snapshots.append(gud_commit.get_metadata_for_snapshot())

        if self.head():
            self.head().children.append(gud_commit.id)

        self.state.head = gud_commit.id
        logging.info("Created commit (%s): %s", gud_commit.id, get_oneliner(commit_msg))
        self.state.commits[gud_commit.id] = gud_commit

        logging.info("Creating history branch: %s", history_branch_name)
        self.repo.create_head(history_branch_name)

        self.save_state()
        return gud_commit

    def restore_snapshot(self, snapshot_hash: str) -> None:
        """Restore the state of the given commit to the specified snapshot."""

        if self.state.merge_conflict_state:
            raise ValueError("Cannot restore snapshot during merge conflict.")

        snapshot = None
        for snapshot in self.head().snapshots:
            if snapshot.hash == snapshot_hash:
                break

        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_hash}")

        logging.info("Restoring snapshot %s - %s", snapshot.hash, snapshot.description)
        self.repo.git.checkout(snapshot.hash, ".")
        self.amend(f"Restore snapshot {snapshot.hash} - {snapshot.description}")

    def snapshot(self, message: str = "") -> None:
        """Take a snapshot of the current commit state and add it to the history branch."""

        self.repo.git.checkout(self.head().history_branch)
        self.repo.git.checkout(self.head().id, ".")
        self.add_changes_to_index()
        snapshot_message = f"Snapshot #{len(self.head().snapshots)}"
        if message:
            snapshot_message += f": {message}"
        history_commit = self.repo.index.commit(snapshot_message)
        new_snapshot = Snapshot(hash=history_commit.hexsha, description=snapshot_message)
        logging.info(
            "Taking snapshot for %s: %s - %s",
            self.head().id,
            new_snapshot.hash,
            new_snapshot.description,
        )
        self.head().snapshots.append(new_snapshot)
        self.repo.git.checkout(self.head().id)
        self.save_state()

    def amend(self, message: str = "") -> None:
        """Amend the commit with current changes, updates hash.

        All descendants of this commit are marked as needing evolve.
        """

        if self.state.merge_conflict_state:
            raise ValueError("Cannot amend during merge conflict.")

        if not self.head():
            return

        if self.head().remote:
            raise InvalidOperationForRemote("Cannot amend remote commits.")

        logging.info("Amending commit %s", self.head().id)

        self.add_changes_to_index()
        self.repo.git.commit("--amend", "--no-edit")

        new_hash = self.repo.head.commit.hexsha
        self.head().old_hash, self.head().hash = self.head().hash, new_hash

        def f(c: GudCommit) -> None:
            c.needs_evolve = True

        self.traverse(self.head().id, f, skip=True)
        self.snapshot(message)

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

    def execute_pending_operations(self) -> None:
        """Execute all the operations that were queued in the gg state."""

        count = 0
        total_ops = len(self.state.pending_operations)

        while self.state.pending_operations:
            count += 1
            op = self.state.pending_operations.pop(0)
            logging.info("Executing op %s of %s: %s", count, total_ops, op)
            if op.type == OperationType.EVOLVE:
                self.update(op.evolve_op.base_commit_id)
                self.evolve(op.evolve_op.target_commit_id)
                if self.state.merge_conflict_state:
                    self.save_state()
                    break
            self.save_state()

    def enqueue_op(self, operation: PendingOperation) -> None:
        self.state.pending_operations.append(operation)
        self.save_state()

    def evolve(self, target_commit_id: Optional[str] = None) -> None:
        """Propagate changes of amended commit onto all descendants."""

        if self.state.merge_conflict_state:
            raise ValueError("Cannot evolve during merge conflict.")

        child: Optional[GudCommit] = None
        if not self.head().children:
            print("No children to evolve.")
            return

        if target_commit_id:
            for child_id in self.head().children:
                if child_id == target_commit_id:
                    child = self.get_commit(child_id)
                    break

            if not child:
                raise ValueError(f"{target_commit_id} it not a child of {self.head().id}")
        else:
            # Recurisvely enqueue evolve operations for all descendants
            def f(c: GudCommit) -> None:
                for child_id in c.children:
                    operation = PendingOperation(
                        type=OperationType.EVOLVE,
                        evolve_op=EvolveOperation(base_commit_id=c.id, target_commit_id=child_id),
                    )

                    self.enqueue_op(operation)

            self.traverse(self.head().id, f)
            self.execute_pending_operations()
            return

        assert child is not None
        if not child.needs_evolve:
            logging.info("No need to evolve.")
            return

        try:
            self.repo.git.rebase("--onto", self.head().hash, child.parent_hash, child.id)
            self.continue_evolve(target_commit_id, self.head().id)
        except GitCommandError as e:
            logging.info("Merge conflict")
            lines = e.stdout.split("\n")
            files = []
            for l in lines:
                if "CONFLICT" in l:
                    files.append(l.split(" ")[-1].replace("'", ""))

            if not files:
                raise Exception(f"Unknown error: {e.stdout}") from e

            self.merge_conflict_begin(self.head(), child, files)

    def continue_evolve(self, target_commit_id: str, parent_id: str) -> None:
        """After changes have been propagated (potentially with conflict
        resolution), update all commit metadata to match the new state.
        """
        child = self.get_commit(target_commit_id)
        parent = self.get_commit(parent_id)

        parent_history_branch = self.head().history_branch
        parent_branch = self.head().id
        child.parent_hash = parent.hash
        self.update(child.id)
        self.head().needs_evolve = False
        self.head().hash = self.repo.head.commit.hexsha

        # Merge commit histories
        self.repo.git.checkout(self.head().history_branch)
        commit_msg = f'"Merge commit {parent_branch}"'
        try:
            self.repo.git.merge("--no-ff", "-m", commit_msg, parent_history_branch)
        except GitCommandError as e:
            assert "CONFLICT" in e.stdout
            self.repo.git.checkout(parent_history_branch, ".")
            self.repo.git.add("-A")
            self.repo.git.commit("-m", commit_msg)

        self.repo.git.checkout(self.head().id)
        self.save_state()
        self.execute_pending_operations()

    def update(self, commit_id: str) -> None:
        if self.state.merge_conflict_state:
            raise ValueError("Cannot update during merge conflict.")

        self.repo.git.checkout(commit_id)
        self.state.head = commit_id
        self.save_state()

    def rebase_continue(self) -> None:
        """Accept the current changes and continue rebase."""

        if not self.state.merge_conflict_state:
            raise ValueError("No rebase in progress")
        for file in self.state.merge_conflict_state.files:
            self.repo.git.add(file)

        logging.info("Continue rebase of %s", self.state.merge_conflict_state)

        with modified_environ(GIT_EDITOR="true"):
            self.repo.git.rebase("--continue")

        incoming = self.state.merge_conflict_state.incoming
        current = self.state.merge_conflict_state.current
        self.state.merge_conflict_state = None
        self.continue_evolve(incoming, current)

    def get_commit(self, id: str) -> GudCommit:
        if id not in self.state.commits:
            raise ValueError(f"Commit not found: {id}")

        return self.state.commits[id]

    def print_status(self) -> None:
        """Print the state of the local branches."""
        print("")
        dirty_state = self.get_dirty_state()

        if dirty_state.modified_files and not self.state.merge_conflict_state:
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
            print("")
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

        name_tags = []
        if commit.remote:
            name_tags.append("Remote")
        if commit == self.head():
            name_tags.append("Current")

        name_annotations = ""
        if name_tags:
            name_annotations = f" [bold yellow]({' '.join(name_tags)})[/bold yellow]"

        line = f"[bold {color}]{commit.id}[/bold {color}]"
        line += f"{needs_evolve}{conflict}{name_annotations}: {commit.get_oneliner()}"
        for snapshot in commit.snapshots:
            vertical = "│" if commit.children else " "
            line += f"\n{vertical} [grey37]{snapshot.hash} : {snapshot.description}[/grey37]"

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
