import inspect
import logging
import os
import shutil
import unittest
from typing import List, Any

import dataclasses

from git import Repo

from salsa.gg.gg import ConfigNotFoundError, GitGud, GitHubRepoMetadata, InvalidOperationForRemote
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


class TestGithubRepoMetadata(unittest.TestCase):
    def test_from_github_url_clone(self) -> None:
        github_repo = GitHubRepoMetadata.from_github_url("https://github.com/juanique/monorepo.git")
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

        self.gg = GitGud.clone(self.remote_repo_path, self.local_repo_path)
        self.gg.repo.git.config("user.email", "test@example.com")
        self.gg.repo.git.config("user.name", "test_user")

    def test_clone(self) -> None:
        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))
        self.assertEqual(["contents-from-remote\n"], get_file_contents(local_filename))
        self.gg.print_status()

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


class TestGitGudLocalOnly(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        make_directory(self.local_repo_path)
        logging.info("Test repo is in %s", self.local_repo_path)

        self.repo = Repo.init(self.local_repo_path)
        self.repo.git.config("user.email", "test@example.com")
        self.repo.git.config("user.name", "test_user")
        self.gg = GitGud.for_clean_repo(self.repo)

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
        self.assertTrue(c2.needs_evolve)
        self.assertTrue(c3.needs_evolve)
        self.assertTrue(c4.needs_evolve)

        self.gg.evolve()

        self.gg.update(c2.id)
        expected = "testing1\nstuff to amend\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))
        expected = "testing1.1\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_2)))

        self.gg.update(c3.id)
        expected = "testing1\nstuff to amend\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_1)))
        expected = "testing1.2\n"
        self.assertEqual(expected, "".join(get_file_contents(filename_3)))

        self.gg.update(c4.id)
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
