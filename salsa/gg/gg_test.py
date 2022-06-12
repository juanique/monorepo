import logging
import os
import shutil
import unittest
from typing import List, Any

import dataclasses

from git import Repo

from salsa.gg.gg import ConfigNotFoundError, GitGud, InvalidOperationForRemote
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


class TestGitGud(unittest.TestCase):
    def setUp(self) -> None:
        remote_root = os.path.join(self.get_test_root(), "remote")
        local_root = os.path.join(self.get_test_root(), "local")

        self.last_index = 0
        self.remote_repo_path = os.path.join(remote_root, REPO_DIR_NAME)
        self.local_repo_path = os.path.join(local_root, REPO_DIR_NAME)

        make_directory(remote_root)
        make_directory(local_root)
        make_directory(self.remote_repo_path)

        self.remote_repo = Repo.init(self.remote_repo_path)
        self.remote_repo.git.config("user.email", "test@example.com")
        self.remote_repo.git.config("user.name", "test_user")
        self.remote_gg = GitGud.for_clean_repo(self.remote_repo)

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


class TestGitGudWithRemote(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        self.remote_filename = self.make_test_filename(self.remote_repo_path)
        append(self.remote_filename, "contents-from-remote")
        self.remote_gg.commit("Initial commit")
        self.gg = GitGud.clone(self.remote_repo_path, self.local_repo_path)

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


class TestGitGudLocalOnly(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        make_directory(self.local_repo_path)
        logging.info(f"Test repo is in {self.local_repo_path}")

        self.repo = Repo.init(self.local_repo_path)
        self.repo.git.config("user.email", "test@example.com")
        self.repo.git.config("user.name", "test_user")
        self.gg = GitGud.for_clean_repo(self.repo)

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
                "id": "initial_commit",
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

        expected = "testing1\n" "testing2\n"
        self.assertEqual(expected, "".join(get_file_contents(filename)))

        # We restore to snapshot 0
        self.gg.restore_snapshot(self.gg.head().snapshots[0].hash)

        expected = "testing1\n"
        self.assertEqual(expected, "".join(get_file_contents(filename)))

        # Each restore creates a new snapshot
        self.assertEqual(len(self.gg.head().snapshots), 5)

        # We restore to snapshot 2
        self.gg.restore_snapshot(self.gg.head().snapshots[2].hash)

        expected = "testing1\n" "testing2\n" "testing3\n"
        self.assertEqual(expected, "".join(get_file_contents(filename)))

        # Each restore creates a new snapshot
        self.assertEqual(len(self.gg.head().snapshots), 6)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
