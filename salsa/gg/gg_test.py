from contextlib import contextmanager
import inspect
import logging
import os
import shutil
import unittest
from typing import Dict, Iterator, List, Any, Tuple

import dataclasses

from git import Repo

from salsa.gg.gg import (
    BadGitGudStateError,
    CommitAlreadyMerged,
    ConfigNotFoundError,
    GitGud,
    GitGudConfig,
    GitHubRepoMetadata,
    GudCommit,
    HostedRepo,
    InvalidOperationForRemote,
    GudPullRequest,
    get_branch_name,
)
from salsa.util.subsets import subset_diff

REPO_DIR_NAME = "repo_dir"


def append(filename: str, contents: str) -> None:
    with open(filename, "a", encoding="utf-8") as file:
        file.write(contents)
        file.write("\n")


def get_file_contents(filename: str) -> List[str]:
    with open(filename, encoding="utf-8") as file:
        return file.readlines()


def set_file_contents(filename: str, contents: str) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        file.write(contents)
        file.write("\n")


def make_directory(dirname: str) -> None:
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname)


class FakeHostedRepo(HostedRepo):
    def __init__(self, repo: Repo) -> None:
        super().__init__("repo_name")
        self.repo = repo
        self.next_id = 0
        self.pull_requests: Dict[str, GudPullRequest] = {}

    def create_pull_request(
        self, title: str, remote_branch: str, remote_base_branch: str
    ) -> GudPullRequest:
        pr_id = str(self.next_id)
        self.next_id += 1
        self.pull_requests[pr_id] = GudPullRequest(
            id=pr_id,
            title=title,
            remote_branch=remote_branch,
            remote_base_branch=remote_base_branch,
            state="DRAFT",
        )
        return self.pull_requests[pr_id]

    def close_pull_request(self, pull_request_id: str) -> None:
        self.pull_requests[pull_request_id].state = "CLOSED"

    def get_pull_request(self, pull_request_id: str) -> GudPullRequest:
        return self.pull_requests[pull_request_id]

    def merge_pull_request(self, pull_request_id: str) -> GudPullRequest:
        pr = self.pull_requests[pull_request_id]

        self.repo.git.checkout(pr.remote_base_branch)
        self.repo.git.merge(pr.remote_branch)
        pr.state = "MERGED"
        pr.merged = True
        pr.merge_commit_sha = self.repo.head.commit.hexsha
        return pr


class TestBranchName(unittest.TestCase):
    def test_branch_name(self) -> None:
        self.assertEqual(get_branch_name("--branch", randomize=False), "branch")
        self.assertEqual(get_branch_name("branch", randomize=False), "branch")
        self.assertEqual(get_branch_name("branch\n", randomize=False), "branch")
        self.assertEqual(get_branch_name("My Branch", randomize=False), "my_branch")
        self.assertEqual(get_branch_name("Pequeña: ramita", randomize=False), "pequena_ramita")

    def test_branch_name_randomized(self) -> None:
        self.assertRegex(get_branch_name("branch"), r"^branch_[0-9a-f]{5}$")


class TestGithubRepoMetadata(unittest.TestCase):
    def test_from_github_url_clone(self) -> None:
        github_repo = GitHubRepoMetadata.from_github_url("https://github.com/juanique/monorepo.git")
        assert github_repo == GitHubRepoMetadata(owner="juanique", name="monorepo")

    def test_from_github_ssh_clone(self) -> None:
        github_repo = GitHubRepoMetadata.from_github_url("git@github.com:juanique/monorepo.git")
        assert github_repo == GitHubRepoMetadata(owner="juanique", name="monorepo")

    def test_from_github_url_web(self) -> None:
        github_repo = GitHubRepoMetadata.from_github_url("https://github.com/juanique/monorepo")
        assert github_repo == GitHubRepoMetadata(owner="juanique", name="monorepo")


class TestGitGud(unittest.TestCase):
    def setUp(self) -> None:
        remote_root = os.path.join(self.get_test_root(), "remote")
        local_root = os.path.join(self.get_test_root(), "local")

        self.last_index = 0
        self.remote_repo_path = os.path.join(remote_root, REPO_DIR_NAME)
        self.local_repo_path = os.path.join(local_root, REPO_DIR_NAME)
        logging.info("Test root is %s", self.get_test_root())

        make_directory(remote_root)
        make_directory(local_root)
        make_directory(self.remote_repo_path)

        self.remote_repo = Repo.init(self.remote_repo_path)
        self.remote_repo.git.config("user.email", "test@example.com")
        self.remote_repo.git.config("user.name", "test_user")
        self.maxDiff = None

    def make_test_filename(self, root: str = None) -> str:
        root = root or self.local_repo_path
        self.last_index += 1
        return os.path.join(root, f"file{self.last_index}.txt")

    def get_test_root(self) -> str:
        return os.path.join("/tmp", "gg_tests", self._testMethodName)

    def assertSubset(self, val1: Any, val2: Any) -> None:
        diff = subset_diff(val1, val2)
        if diff is not None:
            self.fail(str(dataclasses.asdict(diff)))

    def assertLogEquals(self, repo: Repo, expected_log: str) -> None:
        git_log = repo.git.log(
            "--graph", "--pretty=format:%d %s", "--abbrev-commit", "--all", "--no-color"
        )
        expected_log = inspect.cleandoc(expected_log)
        # Clear empty spaces at end of lines
        actual_log = "\n".join([line.strip() for line in git_log.split("\n")])
        logging.info("Git log is \n%s", actual_log)
        self.assertEqual(actual_log, expected_log)

    def assertFileContents(self, filename: str, contents: str) -> None:
        self.assertEqual(contents, "".join(get_file_contents(filename)))

    def assertFileDoesNotExist(self, filename: str) -> None:
        self.assertFalse(os.path.exists(filename))


class TestGitGudWithRemote(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        self.remote_filename = self.make_test_filename(self.remote_repo_path)
        append(self.remote_filename, "contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Initial commit")

        self.hosted_repo = FakeHostedRepo(self.remote_repo)
        gg = GitGud.clone(self.remote_repo_path, self.local_repo_path, self.hosted_repo)
        config = GitGudConfig(randomize_branches=False)
        gg.set_config(config)
        gg.repo.git.config("user.email", "test@example.com")
        gg.repo.git.config("user.name", "test_user")

    @contextmanager
    def gg_instance(self) -> Iterator[GitGud]:
        try:
            gg = self.gg
            yield gg
        finally:
            gg.save_state()

    @property
    def gg(self) -> GitGud:
        gg = GitGud.for_working_dir(self.local_repo_path)
        gg.hosted_repo = self.hosted_repo
        return gg

    def reload(self, commit: GudCommit) -> GudCommit:
        return self.gg.get_commit(commit.id)

    def reload_all(self, *args: GudCommit) -> Tuple[GudCommit, ...]:
        return tuple(self.reload(c) for c in args)


class TestGitGudChecks(TestGitGudWithRemote):
    def test_check_history_branch_out_of_sync(self) -> None:
        """The check_state function raises if the history branch is out of sync
        when it shouldn't."""

        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")
        c1 = self.gg.commit("My first commit")

        self.gg.repo.git.checkout(c1.history_branch)
        append(filename_1, "out-of-sync")
        self.gg.repo.git.commit("-a", "-m", "make history out of sync")
        self.gg.repo.git.checkout(c1.id)

        with self.assertRaises(BadGitGudStateError) as cm:
            self.gg.check_state()

        self.gg.print_status()
        self.assertEqual(
            f"{c1.id} not in sync with its history branch {c1.history_branch}", str(cm.exception)
        )

    def test_missing_parent(self) -> None:
        """Check state function raises if there's a reference to a non existent parent."""

        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")

        with self.gg_instance() as gg:
            c1 = gg.commit("Local change")
            c1.parent_id = "i-dont-exist"

        with self.assertRaises(BadGitGudStateError) as cm:
            self.gg.check_state()

        self.gg.print_status()
        self.assertEqual(
            f"Missing commit i-dont-exist referenced as parent of {c1.id}", str(cm.exception)
        )

    def test_parent_child_mismatch(self) -> None:
        """Check state function raises if there's a parent/child reference mismatch."""

        root = self.gg.root()
        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")
        self.gg.commit("Local change")

        append(filename_1, "testing2")
        c2 = self.gg.commit("Local change 2")

        with self.gg_instance() as gg:
            gg.get_commit(c2.id).parent_id = root.id

        with self.assertRaises(BadGitGudStateError) as cm:
            self.gg.check_state()

        self.gg.print_status()
        self.assertIn("Parent/child mismatch", str(cm.exception))

    def test_multiple_roots(self) -> None:
        """Check state function raises if all commits don't have a single common
        root ancestors."""

        root = self.gg.root()

        # Remote changes
        append(self.remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        # Local changes
        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")
        self.gg.commit("Local change")

        # Get latest master
        self.gg.update(root.id)
        new_master = self.gg.sync()

        # We break the link between the two master commits
        with self.gg_instance() as gg:
            gg.get_commit(root.id).children.remove(new_master.id)
            gg.get_commit(new_master.id).parent_hash = None
            gg.get_commit(new_master.id).parent_id = None

        self.gg.print_status()

        with self.assertRaises(BadGitGudStateError) as cm:
            self.gg.check_state()

        self.assertEqual(
            f"Multiple roots found: {', '.join(sorted({root.id, new_master.id}))}",
            str(cm.exception),
        )


class TestGitGudWithRemoteAndSubmodules(TestGitGudWithRemote):
    def setUp(self) -> None:
        super().setUp()

        self.submodule_root = os.path.join(self.get_test_root(), "submodule")
        self.submodule_repo_path = os.path.join(self.submodule_root, "my_submodule")
        make_directory(self.submodule_repo_path)

        self.submodule_repo = Repo.init(self.submodule_repo_path)
        self.submodule_repo.git.config("user.email", "test@example.com")
        self.submodule_repo.git.config("user.name", "test_user")

        self.submodule_filename = self.make_test_filename(self.submodule_repo_path)
        append(self.submodule_filename, "contents-from-submodule")
        self.submodule_repo.git.add("-A")
        self.submodule_repo.git.commit("-a", "-m", "Initial commit in submodule")

    def tearDown(self) -> None:
        self.gg.check_state()

    def test_submodule_initialized(self) -> None:
        self.gg.repo.git.submodule("add", self.submodule_repo_path, "./a-submodule")
        self.gg.commit("Added submodule.")
        local_filename = os.path.join(
            self.local_repo_path, "a-submodule", os.path.basename(self.submodule_filename)
        )
        self.assertEqual(["contents-from-submodule\n"], get_file_contents(local_filename))

    def test_sync_submodule_in_remote(self) -> None:
        """Can pull submodules that were added in remote."""
        # Submodule added in remote
        self.remote_repo.git.submodule("add", self.submodule_repo_path, "./a-submodule")
        self.remote_repo.git.commit("-m", "Added submodule.")

        # Local commit
        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "content1")
        self.gg.commit("content1")

        append(local_filename_1, "content2")
        self.gg.commit("content2")

        self.gg.sync()
        self.gg.print_status()

        submodule_local_filename = os.path.join(
            self.local_repo_path, "a-submodule", os.path.basename(self.submodule_filename)
        )
        self.assertEqual(
            ["contents-from-submodule\n"],
            get_file_contents(submodule_local_filename),
        )

    def test_update_submodule_in_commit(self) -> None:
        """Different commits may be changing the commit of a submodule. Switching between commits,
        updates the local state to match."""

        self.gg.repo.git.submodule("add", self.submodule_repo_path, "./a-submodule")
        self.gg.commit("Added submodule.")

        submodule_local_filename = os.path.join(
            self.local_repo_path, "a-submodule", os.path.basename(self.submodule_filename)
        )

        c0 = self.gg.head()

        # Submodule change
        append(self.submodule_filename, "more-contents-from-submodule")
        self.submodule_repo.git.add("-A")
        self.submodule_repo.git.commit("-a", "-m", "Added more content")

        # We don't have an api for submodules yet, we can just use git
        assert self.gg.is_dirty() is False
        self.gg.repo.git.submodule("update", "--remote", "--merge")
        assert self.gg.is_dirty()

        self.gg.print_status()
        c1 = self.gg.commit("Update submodule")
        self.gg.print_status()
        assert self.gg.is_dirty() is False

        self.assertEqual(
            ["contents-from-submodule\n", "more-contents-from-submodule\n"],
            get_file_contents(submodule_local_filename),
        )

        self.gg.update(c0.id)
        self.assertEqual(
            ["contents-from-submodule\n"],
            get_file_contents(submodule_local_filename),
        )

        self.gg.update(c1.id)
        self.assertEqual(
            ["contents-from-submodule\n", "more-contents-from-submodule\n"],
            get_file_contents(submodule_local_filename),
        )

        # Remote change to verify we can sync
        remote_filename = self.make_test_filename(self.remote_repo_path)
        remote_local_filename = os.path.join(
            self.local_repo_path, os.path.basename(remote_filename)
        )

        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more content")

        self.gg.sync(all=True)
        self.gg.print_status()

        # Verify after sync
        self.gg.update(c0.id)
        self.assertEqual(
            ["contents-from-submodule\n"],
            get_file_contents(submodule_local_filename),
        )
        self.assertEqual(["more-contents-from-remote\n"], get_file_contents(remote_local_filename))

        self.gg.update(c1.id)
        self.assertEqual(
            ["contents-from-submodule\n", "more-contents-from-submodule\n"],
            get_file_contents(submodule_local_filename),
        )
        self.assertEqual(["more-contents-from-remote\n"], get_file_contents(remote_local_filename))


class TestGitGudWithRemoteNoSubmodules(TestGitGudWithRemote):
    def tearDown(self) -> None:
        self.gg.check_state()

    def test_clone(self) -> None:
        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))
        self.assertEqual(["contents-from-remote\n"], get_file_contents(local_filename))
        self.gg.print_status()

    def test_for_working_directory_repo_subdir(self) -> None:
        directory = os.path.join(self.local_repo_path, "subdir")
        make_directory(directory)
        gg = GitGud.for_working_dir(directory)
        state = gg.get_summary()
        self.assertEqual(state.commit_tree.description, "Initial commit")

    def test_for_working_directory_not_git_directory(self) -> None:
        with self.assertRaises(ConfigNotFoundError) as cm:
            GitGud.for_working_dir("/tmp/i-dont-exist")
        self.assertEqual("No GitGud state for /tmp/i-dont-exist.", str(cm.exception))

    def test_for_working_directory(self) -> None:
        gg = GitGud.for_working_dir(self.local_repo_path)
        state = gg.get_summary()
        self.assertEqual(state.commit_tree.description, "Initial commit")

    def test_amend_remote_fails(self) -> None:
        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")

        with self.assertRaises(InvalidOperationForRemote) as cm:
            self.gg.amend()
        self.assertIn("Cannot amend remote commits", str(cm.exception))

    def test_sync_conflict(self) -> None:
        """Conflicts may appear while syncing from remote and they can be resolved, then evolved."""

        append(self.remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))
        append(local_filename, "more-contents-from-local")
        c1 = self.gg.commit("added local content")

        self.gg.print_status()
        self.gg.sync()
        self.gg.print_status()

        expected = (
            "contents-from-remote\n"
            "<<<<<<< HEAD\n"
            "more-contents-from-remote\n"
            "=======\n"
            "more-contents-from-local\n"
            f">>>>>>> {c1.hash[0:7]} (added local content)\n"
        )

        self.assertEqual(expected, "".join(get_file_contents(local_filename)))

        # Resolve the conflict
        set_file_contents(
            local_filename,
            "contents-from-remote\nmore-contents-from-remote\nmore-contents-from-local\n",
        )

        self.gg.rebase_continue()
        self.gg.print_status()
        c1 = self.gg.get_commit(c1.id)
        assert c1.parent_id is not None
        assert self.gg.get_commit(c1.parent_id).description == "Added more remote content"

        # Expected commit tree
        expected_summary = {
            "commit_tree": {
                "description": "Added more remote content",
                "children": [
                    {"description": "added local content"},
                ],
            }
        }
        self.assertSubset(expected_summary, self.gg.get_summary().dict())

    def test_sync_all_conflict(self) -> None:
        """Regression test for a bug that was causing `gg sync --all` to leave
        the repo in a bad state when there were merge conflicts in some of the
        synced branches."""

        append(self.remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        root = self.gg.head()

        # Unrelated commit
        filename = self.make_test_filename()
        append(filename, "something")
        self.gg.commit("something")

        self.gg.update(root.id)
        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))
        append(local_filename, "more-contents-from-local")
        c1 = self.gg.commit("added local content")

        self.gg.update(root.id)
        self.gg.print_status()
        self.gg.sync(all=True)
        self.gg.print_status()

        expected = (
            "contents-from-remote\n"
            "<<<<<<< HEAD\n"
            "more-contents-from-remote\n"
            "=======\n"
            "more-contents-from-local\n"
            f">>>>>>> {c1.hash[0:7]} (added local content)\n"
        )

        self.assertEqual(expected, "".join(get_file_contents(local_filename)))

        # Resolve the conflict
        set_file_contents(
            local_filename,
            "contents-from-remote\nmore-contents-from-remote\nmore-contents-from-local\n",
        )

        self.gg.rebase_continue()
        self.gg.sync(all=True)
        self.gg.print_status()
        c1 = self.gg.get_commit(c1.id)
        assert c1.parent_id is not None
        assert self.gg.get_commit(c1.parent_id).description == "Added more remote content"

        # Expected commit tree
        expected_summary = {
            "commit_tree": {
                "description": "Added more remote content",
                "children": [
                    {"description": "added local content"},
                    {"description": "something"},
                ],
            }
        }
        self.assertSubset(expected_summary, self.gg.get_summary().dict())

    def test_sync_dirty(self) -> None:
        """Cannot sync on a dirty state."""
        # Remote change
        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more content")

        # local
        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "locally added content")

        with self.assertRaises(ValueError) as cm:
            self.gg.sync()
        self.assertEqual("Cannot sync with uncommited local changes.", str(cm.exception))

    def test_sync_all(self) -> None:
        """When passing all=True to sync(), all local commits are synced."""

        # Remote change
        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more content")

        # local changes
        root = self.gg.head()
        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "locally added content")
        c1 = self.gg.commit("local-1")

        self.gg.update(root.id)
        local_filename_2 = self.make_test_filename(self.local_repo_path)
        append(local_filename_2, "locally added content 2")
        c2 = self.gg.commit("local-2")

        self.gg.print_status()
        self.gg.sync(all=True)
        self.gg.print_status()

        # We should stay in the same commit.
        self.assertEqual(self.gg.head().id, c2.id)

        # Changes from remote should be here.
        local_filename = os.path.join(self.local_repo_path, os.path.basename(remote_filename))
        self.assertEqual(["more-contents-from-remote\n"], get_file_contents(local_filename))

        # And also in the other commit
        self.gg.update(c1.id)
        local_filename = os.path.join(self.local_repo_path, os.path.basename(remote_filename))
        self.assertEqual(["more-contents-from-remote\n"], get_file_contents(local_filename))

        # Expected commit tree
        expected = {
            "commit_tree": {
                "description": "Added more content",
                "children": [
                    {"description": "local-1"},
                    {"description": "local-2"},
                ],
            }
        }
        self.assertSubset(expected, self.gg.get_summary().dict())

    def test_sync_remote(self) -> None:
        """Remote changes can be pulled locally by calling GitGud::sync().

        We only keep track of a single remote commit with no children. Doing a sync on a remote
        branch will by definition track a new remote commit with no children, so if the current one
        is empty, it will be stop being tracked locally."""

        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more content")
        self.gg.sync()

        local_filename = os.path.join(self.local_repo_path, os.path.basename(remote_filename))
        self.assertEqual(["more-contents-from-remote\n"], get_file_contents(local_filename))
        summary = self.gg.get_summary()
        self.gg.print_status()
        self.assertEqual(summary.commit_tree.description, "Added more content")
        self.assertEqual(len(summary.commit_tree.children), 0)

    def test_sync_remote_with_local_changes(self) -> None:
        """Remote changes can be pulled locally by calling GitGud::sync() when
        there are local commits present.

        The remote changes will be tracked under a new commmit nested on the most recent
        remote commit that is currently tracked. Local comits will stay on their corresponding
        ancestors.
        """

        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        self.gg.commit("Added local content")

        self.gg.update(self.gg.state.root)
        self.gg.sync()

        local_filename = os.path.join(self.local_repo_path, os.path.basename(remote_filename))
        self.assertEqual(["more-contents-from-remote\n"], get_file_contents(local_filename))
        summary = self.gg.get_summary()
        self.assertEqual(summary.commit_tree.description, "Initial commit")
        self.assertEqual(summary.commit_tree.children[0].description, "Added more remote content")
        self.assertEqual(summary.commit_tree.children[1].description, "Added local content")

    def test_sync_remote_with_local_changes_and_rebase(self) -> None:
        """Local changes can be rebased off of newer remote commits after syncing."""

        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        local_commit = self.gg.commit("Added local content")

        self.gg.update(self.gg.state.root)
        new_remote_commit = self.gg.sync()

        self.gg.print_status()
        self.gg.rebase(source_id=local_commit.id, dest_id=new_remote_commit.id)
        self.gg.print_status()

        synced_filename = os.path.join(self.local_repo_path, os.path.basename(remote_filename))
        self.assertFileContents(synced_filename, "more-contents-from-remote\n")
        self.assertFileContents(local_filename, "locally added content\n")

    def test_sync_remote_from_commit_with_local_changes(self) -> None:
        """Local changes can be synced to a newer remote ancestor."""

        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        self.gg.commit("Added local content")

        self.gg.print_status()
        self.gg.sync()
        self.gg.print_status()

        synced_filename = os.path.join(self.local_repo_path, os.path.basename(remote_filename))
        self.assertFileContents(synced_filename, "more-contents-from-remote\n")
        self.assertFileContents(local_filename, "locally added content\n")

    def test_sync_more_than_one_remote(self) -> None:
        """Verify that we can have multiple remote commits at the same time and
        pull even more."""

        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        self.gg.commit("Added local content")

        self.gg.update(self.gg.state.root)
        self.gg.sync()

        local_filename_2 = self.make_test_filename(self.local_repo_path)
        append(local_filename_2, "locally added content")
        self.gg.commit("2 Added local content")

        self.gg.sync()

        append(remote_filename, "even-more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added even more remote content")

        self.gg.print_status()
        self.gg.sync()
        self.gg.print_status()

        summary = self.gg.get_summary()
        # We expect something like:
        #
        #  master@b97f3814 (Remote) : Initial commit
        #  ├── added_local_content ↟ : Added local
        #  └── master@9cca2297 (Remote) : Added even more remote
        #      └── 2_added_local_conten ↟ (Current) : 2 Added local conte
        self.assertTrue(summary.commit_tree.id.startswith("master@"))
        self.assertEqual(summary.commit_tree.children[0].id, "added_local_content")
        self.assertTrue(summary.commit_tree.children[1].id.startswith("master@"))
        self.assertEqual(summary.commit_tree.children[1].children[0].id, "2_added_local_conten")

    def test_upstream_branch_prefix(self) -> None:
        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        c1 = self.gg.commit("Added local content")
        config = GitGudConfig(remote_branch_prefix="jemunoz/")
        self.gg.set_config(config)
        self.gg.upload()
        self.assertEqual(self.gg.get_commit(c1.id).upstream_branch, "jemunoz/added_local_content")

    def test_drop(self) -> None:
        """Commits can be dropeed with gg drop. This closes the PR."""

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        c1 = self.gg.commit("Added local content")
        self.gg.upload()
        c1 = self.reload(c1)

        self.gg.drop_commit(c1.id)
        self.assertFalse(c1.id in self.gg.state.commits)
        assert c1.pull_request is not None
        self.assertEqual(self.hosted_repo.pull_requests[c1.pull_request.id].state, "CLOSED")

    def test_upload(self) -> None:
        """A local commit can be uploaded to remote."""

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "locally added content")
        c1 = self.gg.commit("Added local content")
        self.gg.upload()

        c1 = self.reload(c1)
        self.assertTrue(c1.upstream_branch in self.remote_repo.git.branch())
        self.remote_repo.git.checkout(c1.upstream_branch)
        synced_filename = os.path.join(self.remote_repo_path, os.path.basename(local_filename))
        self.assertFileContents(synced_filename, "locally added content\n")

        # There should be a PR created in the hosted repo
        self.assertEqual(len(self.hosted_repo.pull_requests), 1)
        pr_id = list(self.hosted_repo.pull_requests.keys())[0]
        self.assertEqual(self.hosted_repo.pull_requests[pr_id].title, c1.description)

        # Add another commit and also push it
        append(local_filename, "More local content")
        c2 = self.gg.commit("More local content")
        self.assertFalse(self.gg.head().uploaded)
        self.gg.upload()
        self.assertTrue(self.gg.head().uploaded)

        c1, c2 = self.reload_all(c1, c2)
        self.assertTrue(c1.upstream_branch in self.remote_repo.git.branch())
        self.remote_repo.git.checkout(c1.upstream_branch)
        synced_filename = os.path.join(self.remote_repo_path, os.path.basename(local_filename))
        self.assertFileContents(synced_filename, "locally added content\n")

        self.assertTrue(c2.upstream_branch in self.remote_repo.git.branch())
        self.remote_repo.git.checkout(c2.upstream_branch)
        synced_filename = os.path.join(self.remote_repo_path, os.path.basename(local_filename))
        self.assertFileContents(synced_filename, "locally added content\nMore local content\n")

    def test_upload_rebase(self) -> None:
        """Rebasing resets uploaded state."""

        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "commit1")
        c1 = self.gg.commit("commit1")

        local_filename_2 = self.make_test_filename(self.local_repo_path)
        append(local_filename_2, "commit2")
        c2 = self.gg.commit("commit2")

        self.gg.update(c1.id)

        local_filename_3 = self.make_test_filename(self.local_repo_path)
        append(local_filename_3, "commit3")
        c3 = self.gg.commit("commit3")

        self.gg.upload(all_commits=True)
        self.assertTrue(self.gg.get_commit(c1.id).uploaded)
        self.assertTrue(self.gg.get_commit(c2.id).uploaded)
        self.assertTrue(self.gg.get_commit(c3.id).uploaded)

        self.gg.rebase(source_id=c2.id, dest_id=c3.id)
        self.assertTrue(self.gg.get_commit(c1.id).uploaded)
        self.assertFalse(self.gg.get_commit(c2.id).uploaded)
        self.assertTrue(self.gg.get_commit(c3.id).uploaded)

    def test_upload_all(self) -> None:
        """All local commits can be uploaded to remote with a single command."""

        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "locally added content")
        c1 = self.gg.commit("Added local content")

        local_filename_2 = self.make_test_filename(self.local_repo_path)
        append(local_filename_2, "More local content")
        c2 = self.gg.commit("More local content")
        self.gg.upload(all_commits=True)

        c1, c2 = self.reload_all(c1, c2)
        self.assertTrue(c1.upstream_branch in self.remote_repo.git.branch())
        self.remote_repo.git.checkout(c1.upstream_branch)
        synced_filename = os.path.join(self.remote_repo_path, os.path.basename(local_filename_1))
        self.assertFileContents(synced_filename, "locally added content\n")

        self.assertTrue(c2.upstream_branch in self.remote_repo.git.branch())
        self.remote_repo.git.checkout(c2.upstream_branch)
        synced_filename = os.path.join(self.remote_repo_path, os.path.basename(local_filename_2))
        self.assertFileContents(synced_filename, "More local content\n")

    def test_upload_amend_upload(self) -> None:
        """Amends can be uploaded to remote."""

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "content1")
        c1 = self.gg.commit("Added local content")
        self.gg.upload()

        append(local_filename, "content2")
        self.gg.amend()

        self.assertFalse(self.gg.head().uploaded)
        self.gg.upload()
        self.assertTrue(self.gg.head().uploaded)

        c1 = self.reload(c1)
        self.assertTrue(c1.upstream_branch in self.remote_repo.git.branch())
        self.remote_repo.git.checkout(c1.upstream_branch)
        synced_filename = os.path.join(self.remote_repo_path, os.path.basename(local_filename))
        self.assertFileContents(synced_filename, "content1\ncontent2\n")

    def test_sync_merged_commit(self) -> None:
        """When syncing, commits that are merged should go away."""

        local_filename = self.make_test_filename(self.local_repo_path)
        append(local_filename, "content1")
        c1 = self.gg.commit("Added local content")
        self.gg.upload()

        c1 = self.reload(c1)
        assert c1.pull_request is not None
        self.hosted_repo.merge_pull_request(c1.pull_request.id)

        self.gg.print_status()
        self.gg.sync()

        summary = self.gg.get_summary()
        self.assertEqual(summary.commit_tree.description, "Added local content")
        self.assertEqual(len(summary.commit_tree.children), 0)

    def test_sync_merged_commit_with_children(self) -> None:
        """When syncing, commits that are merged should go away."""

        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "content1")
        c1 = self.gg.commit("content1")

        local_filename_2 = self.make_test_filename(self.local_repo_path)
        append(local_filename_2, "content2")
        self.gg.commit("content2")

        self.gg.print_status()
        self.gg.upload(all_commits=True)

        # Merge the first commit in the hosted repo
        c1 = self.reload(c1)
        assert c1.pull_request is not None
        self.hosted_repo.merge_pull_request(c1.pull_request.id)

        self.gg.sync()
        self.gg.print_status()

        summary = self.gg.get_summary()
        expected = {
            "commit_tree": {"description": "content1", "children": [{"description": "content2"}]}
        }
        self.assertSubset(expected, summary.dict())

    def test_sync_merged_not_at_remote_head(self) -> None:
        """Verify that children of a merged commit are rebased to remote head after
        merged commit is dropped."""

        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "content1")
        c1 = self.gg.commit("content1")

        local_filename_2 = self.make_test_filename(self.local_repo_path)
        append(local_filename_2, "content2")
        self.gg.commit("content2")
        self.gg.upload(all_commits=True)

        self.gg.print_status()
        c1 = self.gg.get_commit(c1.id)
        assert c1.pull_request is not None
        self.hosted_repo.merge_pull_request(c1.pull_request.id)

        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more remote content")

        self.gg.print_status()
        self.gg.sync()
        self.gg.print_status()

    def test_amend_merged_commit(self) -> None:
        """Merged commits cannot be ameded."""
        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "content1")
        c1 = self.gg.commit("content1")
        self.gg.upload(all_commits=True)

        c1 = self.gg.get_commit(c1.id)
        assert c1.pull_request is not None
        self.hosted_repo.merge_pull_request(c1.pull_request.id)

        append(local_filename_1, "content2")

        with self.assertRaises(CommitAlreadyMerged):
            self.gg.amend()

    def test_patch_unknown_remote_branch(self) -> None:
        with self.assertRaises(ValueError) as cm:
            self.gg.patch("i-dont-exist")

        self.assertEqual("Unknown remote branch: i-dont-exist", str(cm.exception))

    def test_patch(self) -> None:
        """Remote changes can be patched in locally to be managed by gg."""

        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))

        # Create new branch in remote
        self.remote_repo.git.checkout("-b", "feature_a")
        append(self.remote_filename, "feature-a")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Add feature A")

        # We want to patch it as a commit here
        self.gg.patch("feature_a")

        self.assertEqual(
            ["contents-from-remote\n", "feature-a\n"], get_file_contents(local_filename)
        )
        self.gg.print_status()

    def test_patch_branch_in_future(self) -> None:
        """If the remote change is in the future, the corresponding master commit is created."""

        local_remote_filename = os.path.join(
            self.local_repo_path, os.path.basename(self.remote_filename)
        )

        # Have a local commit
        local_filename_1 = self.make_test_filename(self.local_repo_path)
        append(local_filename_1, "local-content1")
        self.gg.commit("local content 1")

        # Move history forward in remote
        append(self.remote_filename, "time_passing")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "time passes")

        # Create new branch in remote
        self.remote_repo.git.checkout("-b", "feature_a")
        append(self.remote_filename, "feature-a")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Add feature A")

        # We want to patch it as a commit here
        self.gg.patch("feature_a")

        self.assertEqual(
            ["contents-from-remote\n", "time_passing\n", "feature-a\n"],
            get_file_contents(local_remote_filename),
        )
        self.gg.print_status()

    def test_rebase_to_new_master(self) -> None:
        """
        We start with:

        master@0 ----- commit1 ---- commit2

        $ gg update master@0
        $ gg sync
        $ gg rebase -s commit2 -d master@1

        We get:

        master@0 ----- commit1
                \
                  --- master@1 ---- commit2
        """

        root = self.gg.root()

        filename_1 = self.make_test_filename()
        append(filename_1, "commit1")
        self.gg.commit("commit1")

        filename_2 = self.make_test_filename()
        append(filename_2, "commit2")
        c2 = self.gg.commit("commit2")

        # Remote change
        remote_filename = self.make_test_filename(self.remote_repo_path)
        append(remote_filename, "more-contents-from-remote")
        self.remote_repo.git.add("-A")
        self.remote_repo.git.commit("-a", "-m", "Added more content")

        self.gg.update(root.id)
        new_master = self.gg.sync()

        self.gg.print_status()
        self.gg.rebase(source_id=c2.id, dest_id=new_master.id)
        self.gg.print_status(full=True)

        self.gg.check_state()


class TestGitGudLocalOnly(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        make_directory(self.local_repo_path)
        logging.info("Test repo is in %s", self.local_repo_path)

        self.repo = Repo.init(self.local_repo_path)
        self.repo.git.config("user.email", "test@example.com")
        self.repo.git.config("user.name", "test_user")

        gg = GitGud.for_clean_repo(self.repo)
        config = GitGudConfig(randomize_branches=False)
        gg.set_config(config)

    @property
    def gg(self) -> GitGud:
        return GitGud.for_working_dir(self.local_repo_path)

    def reload(self, commit: GudCommit) -> GudCommit:
        return self.gg.get_commit(commit.id)

    def reload_all(self, *args: GudCommit) -> Tuple[GudCommit, ...]:
        return tuple(self.reload(c) for c in args)


class TestGitGudLocalNoChecks(TestGitGudLocalOnly):
    def tearDown(self) -> None:
        self.gg.check_state()

    def test_commit_remove_file(self) -> None:
        """Commits correctly pick up deleted files."""
        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")
        self.gg.commit("My first commit")

        os.remove(filename_1)
        self.gg.commit("Delete file")

    def test_commit(self) -> None:
        """Commits can be created on top of each other.

        $ gg commit -m"Commit message"
        """

        filename_1 = self.make_test_filename()
        filename_2 = self.make_test_filename()
        append(filename_1, "testing1")
        append(filename_1, "testing2")
        append(filename_2, "testing3")

        self.gg.commit("My first commit")

        append(filename_1, "for commit 3")

        self.gg.commit("My second commit")

        summary = self.gg.get_summary()

        expected = {
            "commit_tree": {
                "id": "master",
                "is_head": False,
                "description": "Initial commit",
                "children": [
                    {
                        "id": "my_first_commit",
                        "is_head": False,
                        "description": "My first commit",
                        "children": [
                            {
                                "id": "my_second_commit",
                                "is_head": True,
                                "description": "My second commit",
                            }
                        ],
                    }
                ],
            }
        }
        self.assertSubset(expected, summary.dict())

    def test_update(self) -> None:
        """Can jump back and forth between commits.

        $ gg update commit_name
        """

        filename = self.make_test_filename()

        append(filename, "testing1")
        c1 = self.gg.commit("My first commit")
        append(filename, "testing2")
        c2 = self.gg.commit("My second commit")

        self.assertEqual(["testing1\n", "testing2\n"], get_file_contents(filename))

        self.gg.update(c1.id)
        self.assertEqual(["testing1\n"], get_file_contents(filename))

        self.gg.update(c2.id)
        self.assertEqual(["testing1\n", "testing2\n"], get_file_contents(filename))

    def test_update_dirty(self) -> None:
        """Cannot change commit with dirty local state."""
        filename = self.make_test_filename()
        append(filename, "testing1")
        c1 = self.gg.commit("My first commit")
        append(filename, "testing2")
        self.gg.commit("My second commit")

        self.assertFalse(self.gg.is_dirty())
        append(filename, "testing3")
        self.assertTrue(self.gg.is_dirty())

        with self.assertRaises(ValueError) as cm:
            self.gg.update(c1.id)
        self.assertEqual("Cannot update with uncommited local changes.", str(cm.exception))

    def test_amend_remove_file(self) -> None:
        """Regression test for a bug that caused deleted files not to be
        propagated to the history branch."""

        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")
        c1 = self.gg.commit("My first commit")

        self.gg.update(c1.id)
        os.remove(filename_1)
        self.gg.amend("Delete file1")

        self.gg.print_status()

        append(filename_1, "testing1")
        self.gg.amend("Add file again")

        # History snapshot 1 is when file was deleted
        self.gg.restore_snapshot(self.gg.head().snapshots[1].hash)
        self.assertFileDoesNotExist(filename_1)

        # History snapshot 2 is when file was created again
        self.gg.restore_snapshot(self.gg.head().snapshots[2].hash)
        self.assertFileContents(filename_1, "testing1\n")

    def test_amend_evolve_single_line(self) -> None:
        """Can update old commits and propagate changes on a linear chain.

        $ gg update <old-commit>
        ... change files
        $ gg amend
        ... conflict!
        ... resolve conflict
        $ gg rebase --continue
        """
        filename = self.make_test_filename()

        append(filename, "testing1")
        c1 = self.gg.commit("My first commit")
        append(filename, "testing2")
        c2 = self.gg.commit("My second commit")
        c2_original_hash = c2.hash

        self.gg.update(c1.id)
        append(filename, "testing3")

        self.gg.amend()
        c1, c2 = self.reload_all(c1, c2)
        self.assertTrue(c2.needs_evolve)

        self.gg.evolve()

        # Merge conflict
        expected = (
            "testing1\n"
            "<<<<<<< HEAD\n"
            "testing3\n"
            "=======\n"
            "testing2\n"
            f">>>>>>> {c2.hash[0:7]} (My second commit)\n"
        )

        self.assertEqual(expected, "".join(get_file_contents(filename)))
        set_file_contents(filename, "testing1\ntesting2\ntesting3")
        self.gg.rebase_continue()
        c1, c2 = self.reload_all(c1, c2)

        self.assertEqual(c2.id, self.gg.head().id)
        self.assertFalse(c2.needs_evolve)

        # Hash of commit two should have changed
        self.assertNotEqual(c2_original_hash, self.gg.get_commit(c2.id).hash)

    def test_amend_evolve_single_line_with_conflict_recursive(self) -> None:
        """Can update old commits and propagate changes on a linear chain
        recursively with merge conflicts."""

        filename_1 = self.make_test_filename()
        filename_2 = self.make_test_filename()
        filename_3 = self.make_test_filename()

        append(filename_1, "testing1")
        c1 = self.gg.commit("My first commit")

        append(filename_1, "testing1.1")
        c2 = self.gg.commit("My second commit")

        append(filename_2, "testing1.1.1")
        c3 = self.gg.commit("My third commit")

        append(filename_3, "testing1.1.1.1")
        c4 = self.gg.commit("My fourth commit")

        self.gg.update(c1.id)
        append(filename_1, "more testing1")
        self.gg.amend()

        self.gg.evolve()

        # Merge conflict
        expected = (
            "testing1\n"
            "<<<<<<< HEAD\n"
            "more testing1\n"
            "=======\n"
            "testing1.1\n"
            f">>>>>>> {c2.hash[0:7]} (My second commit)\n"
        )

        self.assertEqual(expected, "".join(get_file_contents(filename_1)))
        set_file_contents(filename_1, "testing1\nmore testing1\ntesting1.1")

        logging.info("User resolves merge conflict")
        self.gg.rebase_continue()
        self.gg.print_status()

        expected = "testing1\nmore testing1\ntesting1.1\n"

        self.gg.update(c2.id)
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))

        self.gg.update(c3.id)
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))

        self.gg.update(c4.id)
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))

        expected_log = """
            *    (history_my_fourth_commit) Evolved changes from my_third_commit
            |\\
            | *    (history_my_third_commit) Evolved changes from my_second_commit
            | |\\
            | | *    (history_my_second_commit) Merge commit my_first_commit
            | | |\\
            | | | *  (history_my_first_commit) Snapshot #1
            * | | |  My fourth commit
            |/ / /
            * / /  My third commit
            |/ /
            * /  My second commit
            |/
            *  My first commit
            | *  (HEAD -> my_fourth_commit) My fourth commit
            | *  (my_third_commit) My third commit
            | *  (my_second_commit) My second commit
            | *  (my_first_commit) My first commit
            |/
            *  (master) Initial commit
        """
        self.assertLogEquals(self.gg.repo, expected_log)

    def test_dirty_state(self) -> None:
        """Untracked and modified files should be shown in the dirty state."""

        # Add an untracked file
        filename = self.make_test_filename()
        relative_filename = os.path.relpath(filename, self.local_repo_path)

        append(filename, "testing1")
        dirty_state = self.gg.get_dirty_state()
        self.assertIn(relative_filename, dirty_state.untracked_files)
        self.assertEqual([], dirty_state.modified_files)

        # After commmit we should be back in a clean state
        self.gg.commit("My first commit")
        dirty_state = self.gg.get_dirty_state()
        self.assertEqual([], dirty_state.untracked_files)
        self.assertEqual([], dirty_state.modified_files)

        # Modify a file
        append(filename, "testing1")
        dirty_state = self.gg.get_dirty_state()
        self.assertEqual([], dirty_state.untracked_files)
        self.assertEqual([relative_filename], dirty_state.modified_files)

    def test_amend_snapshot(self) -> None:
        """Amending commits creates snapshots.

        $ gg commit -m"Commit message"
        ... change files
        $ gg amend
        ... change files
        $ gg amend
        $ gg status # shows snapshots
        $ gg restore <snapshot-hash>
        """

        filename = self.make_test_filename()

        # First commit is snapshot 0
        append(filename, "testing1")
        self.gg.commit("My first commit")
        self.assertEqual(len(self.gg.head().snapshots), 1)

        # Amend is snapshot 1
        append(filename, "testing2")
        self.gg.amend()
        self.assertEqual(len(self.gg.head().snapshots), 2)

        # Seconda amend is snapshot 2
        append(filename, "testing3")
        self.gg.amend()
        self.assertEqual(len(self.gg.head().snapshots), 3)

        self.gg.print_status(full=True)

        # We restore to snapshot 1
        self.gg.restore_snapshot(self.gg.head().snapshots[1].hash)

        expected = "testing1\ntesting2\n"
        self.assertEqual(expected, "".join(get_file_contents(filename)))

        # We restore to snapshot 0
        self.gg.restore_snapshot(self.gg.head().snapshots[0].hash)

        expected = "testing1\n"
        self.assertEqual(expected, "".join(get_file_contents(filename)))

        # Each restore creates a new snapshot
        self.assertEqual(len(self.gg.head().snapshots), 5)

        # We restore to snapshot 2
        self.gg.restore_snapshot(self.gg.head().snapshots[2].hash)

        expected = "testing1\ntesting2\ntesting3\n"
        self.assertEqual(expected, "".join(get_file_contents(filename)))

        # Each restore creates a new snapshot
        self.assertEqual(len(self.gg.head().snapshots), 6)

    def test_amend_multiple_children(self) -> None:
        """Can update old commits and propagate changes on multiple children."""
        filename_1 = self.make_test_filename()
        filename_2 = self.make_test_filename()
        filename_3 = self.make_test_filename()
        filename_4 = self.make_test_filename()

        append(filename_1, "testing1")
        c1 = self.gg.commit("My first commit")

        append(filename_2, "testing1.1")
        c2 = self.gg.commit("My second commit")

        self.gg.update(c1.id)
        append(filename_3, "testing1.2")
        c3 = self.gg.commit("My third commit")

        append(filename_4, "testing1.2.1")
        c4 = self.gg.commit("My fourth commit")

        self.gg.update(c1.id)
        append(filename_1, "stuff to amend")

        self.gg.amend()
        c1, c2, c3, c4 = self.reload_all(c1, c2, c3, c4)
        self.assertTrue(c2.needs_evolve)
        self.assertTrue(c3.needs_evolve)
        self.assertTrue(c4.needs_evolve)

        self.gg.evolve()

        self.gg.update(c2.id)
        c1, c2, c3, c4 = self.reload_all(c1, c2, c3, c4)
        expected = "testing1\nstuff to amend\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))
        expected = "testing1.1\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_2)))

        self.gg.update(c3.id)
        c1, c2, c3, c4 = self.reload_all(c1, c2, c3, c4)
        expected = "testing1\nstuff to amend\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))
        expected = "testing1.2\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_3)))

        self.gg.update(c4.id)
        c1, c2, c3, c4 = self.reload_all(c1, c2, c3, c4)
        expected = "testing1\nstuff to amend\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))
        expected = "testing1.2.1\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_4)))

    def test_rebase(self) -> None:
        """
        We start with:

        master ----- commit1 ---- commit2
               \
                 --- commit3

        $ gg rebase -s commit2 -d commit3

        We get:

        master ----- commit1
               \
                 --- commit3 ---- commit2
        """

        filename_1 = self.make_test_filename()
        append(filename_1, "commit1")
        self.gg.commit("commit1")

        filename_2 = self.make_test_filename()
        append(filename_2, "commit2")
        c2 = self.gg.commit("commit2")

        self.gg.update("master")

        filename_3 = self.make_test_filename()
        append(filename_3, "commit3")
        c3 = self.gg.commit("commit3")

        self.gg.print_status()
        self.gg.rebase(source_id=c2.id, dest_id=c3.id)
        self.gg.print_status()

        self.assertFileContents(filename_3, "commit3\n")
        self.assertFileContents(filename_2, "commit2\n")
        self.assertFileDoesNotExist(filename_1)

    def test_rebase_auto_evolve(self) -> None:
        """
        We start with:

        master ----- commit1 ---- commit2 ---- commit4
               \
                 --- commit3

        $ gg rebase -s commit2 -d commit3

        We get:

        master ----- commit1
               \
                 --- commit3 ---- commit2 ---- commit4
        """

        filename_1 = self.make_test_filename()
        append(filename_1, "commit1")
        self.gg.commit("commit1")

        filename_2 = self.make_test_filename()
        append(filename_2, "commit2")
        c2 = self.gg.commit("commit2")

        filename_4 = self.make_test_filename()
        append(filename_4, "commit4")
        c4 = self.gg.commit("commit4")

        self.gg.update("master")

        filename_3 = self.make_test_filename()
        append(filename_3, "commit3")
        c3 = self.gg.commit("commit3")

        self.gg.print_status()
        self.gg.rebase(source_id=c2.id, dest_id=c3.id)

        self.assertFileDoesNotExist(filename_1)
        self.assertFileContents(filename_2, "commit2\n")
        self.assertFileContents(filename_3, "commit3\n")
        self.assertFileDoesNotExist(filename_4)

        self.gg.update(c4.id)
        self.gg.print_status()
        self.assertFileDoesNotExist(filename_1)
        self.assertFileContents(filename_2, "commit2\n")
        self.assertFileContents(filename_3, "commit3\n")
        self.assertFileContents(filename_4, "commit4\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
