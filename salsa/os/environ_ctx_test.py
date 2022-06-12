# coding: utf-8
import logging
import os
import unittest

from salsa.os.environ_ctx import modified_environ


class TestEnvironCtx(unittest.TestCase):
    def setUp(self):
        os.environ.pop("MODIFIED_ENVIRON", None)

    def tearDown(self):
        os.environ.pop("MODIFIED_ENVIRON", None)

    def test_modified_environ__no_args(self):
        with modified_environ():
            pass

    def test_modified_environ__inserted(self):
        with modified_environ(MODIFIED_ENVIRON="inserted"):
            assert os.environ["MODIFIED_ENVIRON"] == "inserted"
        assert "MODIFIED_ENVIRON" not in os.environ

    def test_modified_environ__updated(self):
        os.environ["MODIFIED_ENVIRON"] = "value"
        with modified_environ(MODIFIED_ENVIRON="updated"):
            assert os.environ["MODIFIED_ENVIRON"] == "updated"
        assert os.environ["MODIFIED_ENVIRON"] == "value"

    def test_modified_environ__deleted(self):
        os.environ["MODIFIED_ENVIRON"] = "value"
        with modified_environ("MODIFIED_ENVIRON"):
            assert "MODIFIED_ENVIRON" not in os.environ
        assert os.environ["MODIFIED_ENVIRON"] == "value"

    def test_modified_environ__deleted_missing(self):
        with modified_environ("MODIFIED_ENVIRON"):
            assert "MODIFIED_ENVIRON" not in os.environ


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
