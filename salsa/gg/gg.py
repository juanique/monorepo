from abc import ABC, abstractmethod
from enum import Enum
import random
import re
from typing import Dict, List, Optional, Callable

import os
import logging
import hashlib
import json

from unidecode import unidecode
from git import Repo, GitCommandError
from pydantic import BaseModel
from rich import print
from rich.tree import Tree
import github
from github import Github

from salsa.os.environ_ctx import modified_environ

CONFIGS_ROOT = os.path.expanduser("~/.config/gg")


class GudPullRequest(BaseModel):
    id: str
    title: str
    remote_branch: str
    remote_base_branch: str
    state: str
    merge_commit_sha: Optional[str]
    merged: bool = False


class CommitAlreadyMerged(Exception):
    pass


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
    parent_id: Optional[str]
    upstream_branch: Optional[str]
    uploaded: bool
    pull_request: Optional[GudPullRequest]

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


class GitHubRepoMetadata(BaseModel):
    owner: str
    name: str

    def get_commit_url(self, commit_hash: str) -> str:
        return f"{self.url}/commit/{commit_hash}"

    def get_pull_request_url(self, pr_id: str) -> str:
        return f"{self.url}/pull/{pr_id}"

    @property
    def full_repo_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"

    @classmethod
    def from_github_url(cls, url: str) -> "GitHubRepoMetadata":
        """Parses a clone url from github and extract the repo metadata."""

        if url.startswith("https"):
            parts = re.findall(r"https://github.com/(.*)/([^\.]*).*", url)
            owner, name = parts[0]
            return cls(owner=owner, name=name)
        if url.startswith("git@"):
            parts = re.findall(r"git@github.com:(.*)/([^\.]*).*", url)
            owner, name = parts[0]
            return cls(owner=owner, name=name)
        raise ValueError(f"Can't parse {url}")


class RepoMetadata(BaseModel):
    github: Optional[GitHubRepoMetadata]


class GitGudConfig(BaseModel):
    remote_branch_prefix: str = ""
    randomize_branches: bool = True
    verbose: bool = False


class RepoState(BaseModel):
    repo_dir: str
    head: str
    root: str
    commits: Dict[str, GudCommit] = {}
    merge_conflict_state: Optional[MergeConflictState] = None
    pending_operations: List[PendingOperation] = []
    master_branch: str = "master"
    repo_metadata: Optional[RepoMetadata]
    config: GitGudConfig = GitGudConfig()

    class Config:
        use_enum_values = True


def get_branch_name(string: str, randomize: bool = True) -> str:
    suffix = ""
    if randomize:
        alphabet = "0123456789abcdef"
        r = random.SystemRandom()
        suffix = "_" + "".join([r.choice(alphabet) for i in range(5)])

    return unidecode(
        string.split("\n")[0][0:20].lower().replace(" ", "_").replace(".", "").replace(":", "")
        + suffix
    )


def get_oneliner(string: str) -> str:
    return string.split("\n")[0][0:40]


class HostedRepo(ABC):
    def __init__(self, repo_name: str):
        self.repo_name = repo_name

    @abstractmethod
    def create_pull_request(
        self, title: str, remote_branch: str, remote_base_branch: str
    ) -> GudPullRequest:
        """Create a pull request on the hosting service. Returns the ID of the
        recently created PR."""

    @abstractmethod
    def close_pull_request(self, pull_request_id: str) -> None:
        """Closes an open pull request."""

    @abstractmethod
    def get_pull_request(self, pull_request_id: str) -> GudPullRequest:
        """Get the pull request metadata."""


class GitHubHostedRepo(HostedRepo):
    def __init__(self, repo_name: str, github_client: Github):
        super().__init__(repo_name)
        self.github = github_client

    def get_pull_request(self, pull_request_id: str) -> GudPullRequest:
        repo = self.github.get_repo(self.repo_name)
        pr = repo.get_pull(int(pull_request_id))
        return self._convert(pr)

    def create_pull_request(
        self, title: str, remote_branch: str, remote_base_branch: str
    ) -> GudPullRequest:
        repo = self.github.get_repo(self.repo_name)
        pr = repo.create_pull(
            title=title,
            body="",
            head=remote_branch,
            base=remote_base_branch,
            draft=True,
        )
        return self._convert(pr)

    def close_pull_request(self, pull_request_id: str) -> None:
        repo = self.github.get_repo(self.repo_name)
        pr = repo.get_pull(int(pull_request_id))
        pr.edit(state="closed")

    def _convert(self, pr: github.PullRequest.PullRequest) -> GudPullRequest:
        pull_request = GudPullRequest(
            id=str(pr.number),
            title=pr.title,
            remote_brAanch=pr.head.ref,
            remote_base_branch=pr.base.ref,
            state=pr.state.upper(),
            merged=pr.merged,
        )

        if pr.merge_commit_sha:
            pull_request.merge_commit_sha = pr.merge_commit_sha

        return pull_request


class GitGud:
    repo: Repo
    state: RepoState

    def __init__(self, repo: Repo, state: RepoState, hosted_repo: Optional[HostedRepo] = None):
        self.repo = repo
        self.state = state
        self.hosted_repo = hosted_repo

        if self.state.config.verbose:
            logging.basicConfig(level=logging.INFO)

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

    def get_config(self) -> GitGudConfig:
        return self.state.config

    def set_config(self, config: GitGudConfig) -> None:
        self.state.config = config
        self.save_state()

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
    def get_remote_commit(repo: Repo, remote_master: str) -> GudCommit:
        master_commit_id = f"master@{repo.head.commit.hexsha[0:8]}"
        new_branch = repo.create_head(master_commit_id)
        new_branch.checkout()

        return GudCommit(
            id=master_commit_id,
            hash=repo.head.commit.hexsha,
            description=repo.head.commit.message.strip(),
            remote=True,
            uploaded=True,
            history_branch=master_commit_id,
            upstream_branch=remote_master,
        )

    @staticmethod
    def get_hosted_repo(repo_metadata: Optional[RepoMetadata]) -> Optional[HostedRepo]:
        """Given the metadata for the remote repo being tracked, get an instance
        of the repo api."""

        if not repo_metadata:
            return None

        if repo_metadata.github:
            if "GITHUB_GG_TOKEN" not in os.environ:
                raise ValueError("Missing env variable GITHUB_GG_TOKEN")

            github_client = Github(os.environ["GITHUB_GG_TOKEN"])
            return GitHubHostedRepo(repo_metadata.github.full_repo_name, github_client)

        return None

    @staticmethod
    def clone(
        remote_repo_path: str, local_repo_path: str, hosted_repo: Optional[HostedRepo] = None
    ) -> "GitGud":
        """Clone an external repo into the given path."""
        repo_metadata = None
        if "github" in remote_repo_path:
            github_repo = GitHubRepoMetadata.from_github_url(remote_repo_path)
            repo_metadata = RepoMetadata(github=github_repo)
            hosted_repo = GitGud.get_hosted_repo(repo_metadata)

        repo = Repo.clone_from(remote_repo_path, local_repo_path)
        root = GitGud.get_remote_commit(repo, repo.active_branch.name)

        state = RepoState(
            repo_dir=local_repo_path,
            root=root.id,
            head=root.id,
            commits={root.id: root},
            repo_metadata=repo_metadata,
        )
        gg = GitGud(repo, state, hosted_repo)
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
        branch_name = repo.active_branch.name
        root = GudCommit(id=branch_name, hash=commit.hexsha, description=commit_msg, uploaded=True)
        state = RepoState(
            repo_dir=repo.working_tree_dir, root=root.id, head=root.id, commits={root.id: root}
        )
        return GitGud(repo, state)

    @staticmethod
    def for_working_dir(working_dir: str) -> "GitGud":
        """Resume a GitGud instance for a previously cloned directory."""

        repo_state = GitGud.load_state_for_directory(working_dir)
        repo = Repo(working_dir)
        hosted_repo = GitGud.get_hosted_repo(repo_state.repo_metadata)
        return GitGud(repo, repo_state, hosted_repo)

    def get_oldest_non_remote(self, commit_id: str) -> GudCommit:
        """Given a commit id, find the oldest ancestor that is not remote."""

        commit = self.get_commit(commit_id)

        if commit.remote:
            raise ValueError(f"Commit {commit_id} is remote")

        if not commit.parent_id:
            return commit

        parent = self.get_commit(commit.parent_id)
        while not parent.remote:
            commit = parent
            if not commit.parent_id:
                raise ValueError("Could not find a non remote ancestor.")

            parent = self.get_commit(commit.parent_id)

        return commit

    def upload(self, commit_id: Optional[str] = None, all_commits: bool = False) -> None:
        """Upload commit changes to remote."""

        if commit_id and all_commits:
            raise ValueError("Use commit_id or all_commits, not both")

        if all_commits:

            def f(c: GudCommit) -> None:
                if not c.remote:
                    self.upload(commit_id=c.id)

            self.traverse(self.root().id, f, skip=False)
            return

        if not commit_id:
            commit_id = self.head().id

        logging.info("Uploading commit %s", commit_id)

        previous_head_id = self.head().id
        commit = self.get_commit(commit_id)

        self.repo.git.checkout(commit.history_branch)
        if not commit.upstream_branch:
            commit.upstream_branch = self.get_config().remote_branch_prefix + commit.id
            self.repo.git.push("-u", "origin", f"{commit.history_branch}:{commit.upstream_branch}")
            if self.hosted_repo:
                logging.info("Creating PR in hosted repo.")
                assert commit.parent_id is not None
                base_commit = self.get_commit(commit.parent_id)

                if not base_commit.upstream_branch:
                    raise ValueError("Can't upload commit. Parent is not uploaded, use --all")

                commit.pull_request = self.hosted_repo.create_pull_request(
                    commit.description, commit.upstream_branch, base_commit.upstream_branch
                )
            else:
                logging.info("No hosted repo, skipping PR creation")
        else:
            self.repo.git.push("origin", f"{commit.history_branch}:{commit.upstream_branch}")

        self.get_commit(commit_id).uploaded = True
        self.update(previous_head_id)
        self.save_state()

    def _sync_pr_state(self, commit: GudCommit) -> None:
        if not commit.pull_request:
            logging.info("Nothing to sync. Commit has no PR.")
            return

        assert self.hosted_repo is not None
        commit.pull_request = self.hosted_repo.get_pull_request(commit.pull_request.id)

    def comes_before(self, commit_1: GudCommit, commit_2: GudCommit) -> bool:
        """Returns True if commit_1 comes before commit_2."""
        self.repo.git.checkout(self.state.master_branch)
        revcount = int(self.repo.git.rev_list("--count", f"{commit_1.hash}..{commit_2.hash}"))
        result = revcount > 0
        return result

    def _insert_remote_commit(self, commit: GudCommit) -> None:
        logging.info("Inserting remote commit %s", commit.id)
        parent = self.root()

        next_child = None
        while True:
            next_parent: Optional[GudCommit] = None

            for child_id in parent.children:
                child = self.get_commit(child_id)
                if not child.remote:
                    continue
                next_parent = child
                break

            if not next_parent:
                break

            if not self.comes_before(next_parent, commit):
                next_child = next_parent
                break

            parent = next_parent

        logging.info("Will insert under %s", parent.id)
        self.state.commits[commit.id] = commit
        parent.children.append(commit.id)
        commit.parent_hash = parent.hash
        commit.parent_id = parent.id

        if next_child:
            self.rebase(source_id=next_child.id, dest_id=commit.id)

    def _rebase_merged_commit(self, commit: GudCommit) -> GudCommit:
        assert commit.pull_request is not None

        if commit.pull_request.state != "MERGED":
            raise ValueError("Pull request is not merged.")

        if not commit.pull_request.merge_commit_sha:
            raise ValueError("Missing merge commit SHA")

        self.repo.git.checkout(commit.pull_request.merge_commit_sha)
        pulled_commit = GitGud.get_remote_commit(self.repo, self.state.master_branch)

        if pulled_commit.id in self.state.commits:
            merged_commit = self.get_commit(pulled_commit.id)
        else:
            self._insert_remote_commit(pulled_commit)
            merged_commit = pulled_commit

        # TODO: Handle rebase conflicts which may happen if the commit was modified after merge
        self.rebase(commit.id, merged_commit.id)
        diff = self.repo.git.diff(commit.id, merged_commit.id)
        if diff:
            raise ValueError("Not implemented.")

        for child_id in commit.children:
            self.rebase(child_id, merged_commit.id)

        self.drop_commit(commit.id)
        return merged_commit

    def sync(self) -> GudCommit:
        """Pull changes from remote and rebase the current commit to a more recent master branch."""
        logging.info("Syncing branch.")

        if self.head().remote:
            commit = self.pull_remote(prune=False)
            self.prune_commits()
            self.save_state()
            return commit

        starting_commit_id = self.head().id
        new_remote_commit = self.pull_remote()
        root = self.get_oldest_non_remote(starting_commit_id)

        if root.pull_request:
            assert self.hosted_repo is not None
            self._sync_pr_state(root)
            logging.info("Commit has pull request and it's %s", root.pull_request.state)
            if root.pull_request.merged:
                merged_commit = self._rebase_merged_commit(root)

                for child_id in merged_commit.children:
                    self.update(child_id)
                    self.sync()

                return merged_commit

        self.rebase(source_id=root.id, dest_id=new_remote_commit.id)
        self.prune_commits()
        self.save_state()
        return new_remote_commit

    def prune_commits(self) -> None:
        """Clean up irrelevant commits.

        - Nested remote commits with no local changes. We only care about the
        most recent one
        """
        logging.info("Checking for commits to prune")
        if len(self.state.commits.keys()) == 1:
            # Always need to have at least one commit
            return

        to_prune: List[str] = []
        for commit_id, commit in self.state.commits.items():
            non_remote_children = list(
                filter(lambda child_id: not self.get_commit(child_id).remote, commit.children)
            )
            if commit.children and commit.remote and not non_remote_children:
                to_prune.append(commit_id)

        for commit_to_prune_id in to_prune:
            logging.info("Prunning commit %s", commit_to_prune_id)
            commit_to_prune = self.get_commit(commit_to_prune_id)

            for commit_id, commit in self.state.commits.items():
                if commit.parent_id == commit_to_prune_id:

                    if not self.state.root == commit_to_prune.id:
                        assert commit_to_prune.parent_id is not None
                        parent_of_prunned = self.get_commit(commit_to_prune.parent_id)
                        commit.parent_id = parent_of_prunned.id
                        commit.parent_hash = parent_of_prunned.hash
                        parent_of_prunned.children.append(commit.id)

                if commit_to_prune_id in commit.children:
                    commit.children.remove(commit_to_prune_id)

            if self.state.root == commit_to_prune.id:
                self.state.root = commit_to_prune.children[0]

            self.state.commits.pop(commit_to_prune_id)
            self.repo.git.branch("-D", commit_to_prune.id)

    def pull_remote(self, prune: bool = True) -> GudCommit:
        """Pulls the latest commit from remote master and adds it as a child of
        the most recent remote commit."""

        # Get the newest remote commit
        newest_remote = None
        for commit in self.state.commits.values():
            if commit.remote:
                if not newest_remote:
                    newest_remote = commit
                    continue

                if self.comes_before(newest_remote, commit):
                    newest_remote = commit
                    continue

        if not newest_remote:
            raise ValueError("No remote commits")

        logging.info("Starting of more recent remote commit %s", newest_remote.id)

        self.repo.git.checkout(self.state.master_branch)
        self.repo.git.pull("--rebase", "origin", self.state.master_branch)
        pulled_commit = GitGud.get_remote_commit(self.repo, self.state.master_branch)
        if pulled_commit.id == newest_remote.id:
            logging.info("Nothing to do, already at latest remote HEAD")
            return newest_remote

        self.state.commits[pulled_commit.id] = pulled_commit
        newest_remote.children.insert(0, pulled_commit.id)
        pulled_commit.parent_hash = newest_remote.hash
        pulled_commit.parent_id = newest_remote.id
        if prune:
            self.prune_commits()
        self.update(pulled_commit.id)
        self.save_state()
        return pulled_commit

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
        branch_name = get_branch_name(commit_msg, self.state.config.randomize_branches)
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
            parent_id=self.head().id,
            uploaded=False,
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
        self._copy_branch_state(snapshot_hash, self.head().id)
        self.amend(f"Restore snapshot {snapshot.hash} - {snapshot.description}")

    def _copy_branch_state(self, source_branch: str, dest_branch: str) -> None:
        temp_branch_name = "temp_" + dest_branch
        self.repo.git.switch("-c", temp_branch_name, source_branch)
        self.repo.git.reset("--soft", dest_branch)
        self.repo.git.branch("-M", dest_branch)

    def snapshot(self, message: str = "", commit: bool = True) -> None:
        """Take a snapshot of the current commit state and add it to the history branch."""

        snapshot_message = f"Snapshot #{len(self.head().snapshots)}"
        if message:
            snapshot_message += f": {message}"

        if commit:
            history_branch = self.head().history_branch
            assert history_branch is not None
            self._copy_branch_state(self.head().id, history_branch)
            self.repo.git.commit("-m", snapshot_message)

        hash = self.repo.head.commit.hexsha
        new_snapshot = Snapshot(hash=hash, description=snapshot_message)
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

        self._sync_pr_state(self.head())
        pr = self.head().pull_request
        if pr and pr.merged:
            raise CommitAlreadyMerged("Cannot amend merged commits.")

        logging.info("Amending commit %s", self.head().id)

        self.add_changes_to_index()
        self.repo.git.commit("--amend", "--no-edit", "--allow-empty")

        new_hash = self.repo.head.commit.hexsha
        self.head().old_hash, self.head().hash = self.head().hash, new_hash

        def f(c: GudCommit) -> None:
            c.needs_evolve = True

        self.traverse(self.head().id, f, skip=True)
        self.head().uploaded = False
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

    def schedule_recursive_evolve(self, commit: GudCommit, mark_as_needed: bool = False) -> None:
        """
        Recurisvely enqueue evolve operations for all descendants.
        """

        logging.info("Scheduling recursive evolve for %s", commit.id)

        def f(c: GudCommit) -> None:
            for child_id in c.children:
                child_commit = self.get_commit(child_id)
                if mark_as_needed and not child_commit.remote:
                    child_commit.needs_evolve = True
                    self.get_commit(child_id).needs_evolve = True

                if not child_commit.remote:
                    operation = PendingOperation(
                        type=OperationType.EVOLVE,
                        evolve_op=EvolveOperation(base_commit_id=c.id, target_commit_id=child_id),
                    )

                    self.enqueue_op(operation)

        self.traverse(commit.id, f)

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
            self.schedule_recursive_evolve(self.head())
            self.execute_pending_operations()
            return

        assert child is not None
        if not child.needs_evolve:
            logging.info("No need to evolve.")
            return

        logging.info("Envolving %s to %s", self.head().id, child.id)

        try:
            self.repo.git.rebase("--onto", self.head().hash, child.parent_hash, child.id)
            self.continue_evolve(
                target_commit_id, self.head().id, f"Evolved changes from {self.head().id}"
            )
        except GitCommandError as e:
            self.handle_merge_conflict(self.head(), child, e)

    def handle_merge_conflict(
        self, current: GudCommit, incoming: GudCommit, error: GitCommandError
    ) -> None:
        """Parse the output of the merge conflict error message into the GitGud
        internal state."""

        logging.info("Merge conflict")
        lines = error.stdout.split("\n")
        files = []
        for l in lines:
            if "CONFLICT" in l:
                files.append(l.split(" ")[-1].replace("'", ""))

        if not files:
            raise Exception(f"Unknown error: {error.stdout}") from error

        self.merge_conflict_begin(current, incoming, files)

    def rebase(self, source_id: str, dest_id: str) -> None:
        """Change the parent commit of the given source commit to be the
        destination commit."""

        logging.info("Rebase %s to %s", source_id, dest_id)
        source_commit = self.get_commit(source_id)
        dest_commit = self.get_commit(dest_id)

        if source_commit.remote:
            if not dest_commit.remote:
                raise ValueError("Remote commits can only be rebased to other remote commits.")

            if not self.comes_before(dest_commit, source_commit):
                raise ValueError(
                    f"{dest_commit.id} does not come before {source_commit.id}, cannot rebase"
                )

            if source_commit.parent_id:
                self.get_commit(source_commit.parent_id).children.remove(source_commit.id)

            dest_commit.children.append(source_commit.id)
            source_commit.parent_id = dest_commit.parent_id
            source_commit.parent_hash = dest_commit.parent_hash
            return

        assert source_commit.parent_id is not None

        try:
            self.schedule_recursive_evolve(source_commit, mark_as_needed=True)
            self.repo.git.rebase(
                "--onto", dest_commit.hash, source_commit.parent_hash, source_commit.id
            )
            self.state.commits[source_commit.parent_id].children.remove(source_commit.id)
            self.state.commits[dest_commit.id].children.append(source_commit.id)
            self.continue_evolve(
                source_commit.id,
                dest_commit.id,
                f"Rebased from {source_commit.parent_id} to {dest_commit.id}",
            )
            self.execute_pending_operations()
            logging.info("Switching to update %s", source_id)
            self.update(source_id)
        except GitCommandError as e:
            self.handle_merge_conflict(source_commit, dest_commit, e)

    def drop_commit(self, commit_id: str) -> None:
        """Drop a commit and close the associated pull request."""

        commit = self.get_commit(commit_id)
        self._sync_pr_state(commit)

        if commit.remote:
            raise ValueError("Cannot drop remote commits")

        if len(self.state.commits.keys()) == 1:
            raise ValueError("Cannot drop only commit")

        if commit.children:
            raise ValueError("Cannot drop commit with children.")

        if commit.id == self.head().id:
            assert commit.parent_id is not None
            self.update(commit.parent_id)

        if commit.pull_request:
            assert self.hosted_repo is not None
            if commit.pull_request.state != "MERGED":
                self.hosted_repo.close_pull_request(commit.pull_request.id)

        for other_commit in self.state.commits.values():
            if commit.id in other_commit.children:
                other_commit.children.remove(commit.id)

        self.state.commits.pop(commit.id)
        self.save_state()

    def continue_evolve(self, target_commit_id: str, parent_id: str, commit_msg: str = "") -> None:
        """After changes have been propagated (potentially with conflict
        resolution), update all commit metadata to match the new state.
        """
        child = self.get_commit(target_commit_id)
        parent = self.get_commit(parent_id)

        child.parent_hash = parent.hash
        child.parent_id = parent.id
        self.update(child.id)
        child.hash = self.repo.head.commit.hexsha
        self.head().needs_evolve = False
        self.head().uploaded = False
        self.head().hash = self.repo.head.commit.hexsha

        # Merge commit histories
        self.repo.git.checkout(child.history_branch)
        commit_msg = commit_msg or f"Merge commit {parent.id}"
        try:
            self.repo.git.merge("--no-ff", "-m", commit_msg, parent.history_branch)
        except GitCommandError as e:
            assert "CONFLICT" in e.stdout

            # This is just a quick way to get out the merge state, we amend this
            # commit right after. This is because we can't do `_copy_branch_state()`
            # during conflict resolution since it switches branches.
            self.repo.git.checkout(child.id, ".")
            self.repo.git.add("-A")
            self.repo.git.commit("-m", commit_msg)

            # We get the actual desired state.
            assert child.history_branch is not None
            self._copy_branch_state(child.id, child.history_branch)
            self.repo.git.commit("--amend", "-a", "--no-edit")

        self.repo.git.checkout(child.id)
        self.snapshot(commit_msg, commit=False)
        self.save_state()
        self.execute_pending_operations()

        self.prune_commits()
        self.save_state()

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

    def print_status(self, full: bool = False) -> None:
        """Print the state of the local branches."""
        print("")
        dirty_state = self.get_dirty_state()

        symbols: Dict[str, str] = {}
        for commit in self.state.commits.values():
            if not commit.uploaded:
                symbols["↟"] = "Needs upload"
            if commit.needs_evolve:
                symbols["×"] = "Needs evolve"

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

        if symbols:
            print("Legend:")
            for symbol, explanation in symbols.items():
                print(f" [bold red]{symbol}[/bold red]: {explanation}")
            print("")

        tree = self.get_tree(full=full)
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

    def get_tree(self, commit: GudCommit = None, tree: Tree = None, full: bool = False) -> Tree:
        """Return a tree representation of the local gitgud state for printing."""

        commit = commit or self.root()
        color = "green" if commit == self.head() else "magenta"

        needs_evolve = ""
        if commit.needs_evolve and not self.state.merge_conflict_state:
            needs_evolve = " ×"

        needs_upload = ""
        if not commit.uploaded:
            needs_upload = " ↟"

        conflict = ""
        if self.state.merge_conflict_state:
            conflict_type = ""
            if commit.id == self.state.merge_conflict_state.current:
                conflict_type = "current"
            if commit.id == self.state.merge_conflict_state.incoming:
                conflict_type = "incoming"
            if self.state.merge_conflict_state and conflict_type:
                conflict = f" ({conflict_type})"

        name_tags = []
        url = ""
        if commit.remote:
            name_tags.append("Remote")
            if self.state.repo_metadata and self.state.repo_metadata.github:
                url = self.state.repo_metadata.github.get_commit_url(commit.hash[0:5])
                url = f"[bold]{url}[/bold]"

        if (
            not commit.remote
            and commit.pull_request
            and self.state.repo_metadata
            and self.state.repo_metadata.github
        ):
            url = self.state.repo_metadata.github.get_pull_request_url(commit.pull_request_id)
            url = f"[bold]{url}[/bold]"

        if commit == self.head():
            name_tags.append("Current")

        name_annotations = ""
        if name_tags:
            name_annotations = f" [bold yellow]({' '.join(name_tags)})[/bold yellow]"

        line = f"[bold {color}]{commit.id}[/bold {color}]"
        line += f"[bold red]{needs_evolve}{needs_upload}{conflict}[/bold red]{name_annotations} "
        line += f"{url}: {commit.get_oneliner()}"
        if full:
            for snapshot in commit.snapshots:
                vertical = "│" if commit.children else " "
                line += f"\n{vertical} [grey37]{snapshot.hash} : {snapshot.description}[/grey37]"

        if not tree:
            branch = Tree(line)
        else:
            branch = tree.add(line)

        for child_id in commit.children:
            self.get_tree(self.get_commit(child_id), branch, full=full)

        return branch

    def get_dirty_state(self) -> DirtyState:
        state = DirtyState()
        for item in self.repo.index.diff(None):
            state.modified_files.append(item.a_path)

        for untracked in self.repo.untracked_files:
            state.untracked_files.append(untracked)

        return state
