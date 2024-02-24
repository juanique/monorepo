import sys
import os
import pytest
from shutil import copyfile


# if using 'bazel test ...'
if __name__ == "__main__":
    args = ["--capture=no", "--pylint"] + sys.argv[1:]
    sys.exit(pytest.main(args))

