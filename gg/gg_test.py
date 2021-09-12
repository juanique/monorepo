import os
import shutil
import unittest
from git import Repo
from gg import GitGud, GudCommit

REPO_DIR_NAME = "repo_dir"


def append(filename, contents):
    with open(filename, "a") as file:
        file.write(contents)
        file.write("\n")


def get_file_contents(filename):
    with open(filename) as file:
        return file.readlines()


def set_file_contents(filename, contents):
    with open(filename, "w") as file:
        file.write(contents)
        file.write("\n")


def make_directory(dirname):
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname)


class TestGitGud(unittest.TestCase):
    def setUp(self):
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

    def make_test_filename(self, root=None):
        root = root or self.local_repo_path
        self.last_index += 1
        return os.path.join(root, f"file{self.last_index}.txt")

    def get_test_root(self):
        return os.path.join("/tmp", "gg_tests", self._testMethodName)


class TestGitGudWithRemote(TestGitGud):
    def setUp(self):
        super().setUp()

        self.remote_filename = self.make_test_filename(self.remote_repo_path)
        append(self.remote_filename, "contents-from-remote")
        self.remote_gg.commit("Initial commit")
        self.repo = Repo.clone_from(self.remote_repo_path, self.local_repo_path)
        self.gg = GitGud(self.repo)

    def test_clone(self):
        local_filename = os.path.join(self.local_repo_path, os.path.basename(self.remote_filename))
        self.assertEqual(["contents-from-remote\n"], get_file_contents(local_filename))
        self.gg.print_status()


class TestGitGudLocalOnly(TestGitGud):
    def setUp(self):
        super().setUp()

        make_directory(self.local_repo_path)
        self.repo = Repo.init(self.local_repo_path)
        self.repo.git.config("user.email", "test@example.com")
        self.repo.git.config("user.name", "test_user")
        self.gg = GitGud(self.repo)

    def test_commit(self):
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

    def test_update(self):
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

    def test_amend_evolve_single_line(self):
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

        self.assertEqual(c2.id, self.gg.head.id)
        self.assertFalse(c2.needs_evolve)


if __name__ == "__main__":
    unittest.main()
