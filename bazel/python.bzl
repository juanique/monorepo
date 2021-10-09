load("@subpar//:subpar.bzl", "par_binary")
load("@mypy_integration//:mypy.bzl", "mypy_test")

def py_binary(name, **kwargs):
    """ Wrapper for py_binary rule that adds additional functionality.

    Two additional targets are added, one for .par target and one for mypy check
    test.

    Args:
     name: Name that will be used for the native py_binary target.
     **kwargs: All other target args.
    """

    if "main" not in kwargs:
        if len(kwargs.get("srcs")) == 1:
            kwargs["main"] = kwargs["srcs"][0]
        else:
            fail("Missing main attribute for multi srcs target.")

    native.py_binary(name = name, **kwargs)
    mypy_test(name = name + "_mypy", deps = [":" + name])
    par_binary(name = name + "_par", imports = [""], **kwargs)

def py_library(name, **kwargs):
    native.py_library(name = name, **kwargs)
    mypy_test(name = name + "_mypy", deps = [":" + name])

def py_test(name, **kwargs):
    native.py_test(name = name, **kwargs)
    mypy_test(name = name + "_mypy", deps = [":" + name])
