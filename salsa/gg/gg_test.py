import os
import shutil
from typing import List
import unittest
from git import Repo
from salsa.gg.gg import GitGud

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
        self.remote_gg = GitGud(self.remote_repo)

    def make_test_filename(self, root: str = None) -> str:
        root = root or self.local_repo_path
        self.last_index += 1
        return os.path.join(root, f"file{self.last_index}.txt")

    def get_test_root(self) -> str:
        return os.path.join("/tmp", "gg_tests", self._testMethodName)


class TestGitGudWithRemote(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        self.remote_filename = self.make_test_filename(self.remote_repo_path)
        append(self.remote_filename, "contents-from-remote")
        self.remote_gg.commit("Initial commit")
        self.repo = Repo.clone_from(self.remote_repo_path, self.local_repo_path)
        self.gg = GitGud.forWorkingDir(self.local_repo_path)

    def test_clone(self) -> None:
        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))
        self.assertEqual(["contents-from-remote\n"], get_file_contents(local_filename))
        self.gg.print_status()

    def test_amend_remote_fails(self) -> None:
        filename_1 = self.make_test_filename()
        append(filename_1, "testing1")

        # TODO: Finish this
        # with self.assertRaises(Exception) as e:
        # self.gg.amend()


class TestGitGudLocalOnly(TestGitGud):
    def setUp(self) -> None:
        super().setUp()

        make_directory(self.local_repo_path)
        self.repo = Repo.init(self.local_repo_path)
        self.repo.git.config("user.email", "test@example.com")
        self.repo.git.config("user.name", "test_user")
        self.gg = GitGud(self.repo)

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

        self.assertEqual("initial_commit", self.gg.root.id)
        self.assertEqual("Initial commit", self.gg.root.description)
        self.assertEqual("My first commit", self.gg.root.children[0].description)
        self.assertEqual("My second commit", self.gg.root.children[0].children[0].description)

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
            ">>>>>>> My second commit\n"
        )

        self.assertEqual(expected, "".join(get_file_contents(filename)))
        set_file_contents(filename, "testing1\ntesting2\ntesting3")
        self.gg.rebase_continue()

        self.assertEqual(c2.id, self.gg.head and self.gg.head.id)
        self.assertFalse(c2.needs_evolve)


if __name__ == "__main__":
    unittest.main()
