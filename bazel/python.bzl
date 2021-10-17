load("@pip_deps//:requirements.bzl", "requirement")
load("@mypy_integration//:mypy.bzl", "mypy_test")

def py_binary(name, **kwargs):
    """ Wrapper for py_binary rule that adds additional functionality.

    Two additional targets are added, one for .par target and one for mypy check
    test.

    Args:
     name: Name that will be used for the native py_binary target.
     **kwargs: All other target args.
    """

    if "srcs" not in kwargs:
        fail("Missing srcs.")

    if "main" not in kwargs:
        if len(kwargs.get("srcs")) == 1:
            kwargs["main"] = kwargs["srcs"][0]
        else:
            fail("Missing main attribute for multi srcs target.")

    native.py_binary(name = name, **kwargs)
    mypy_test(name = name + "_mypy", deps = [":" + name])

    # par_binary(name = name + "_par", imports = [""], **kwargs)
    pylint_test(name = name + "_pylint", **kwargs)

def py_library(name, **kwargs):
    native.py_library(name = name, **kwargs)
    mypy_test(name = name + "_mypy", deps = [":" + name])
    pylint_test(name = name + "_pylint", **kwargs)

def py_test(name, **kwargs):
    native.py_test(name = name, **kwargs)
    mypy_test(name = name + "_mypy", deps = [":" + name])
    pylint_test(name = name + "_pylint", **kwargs)

def pylint_test(name, srcs, deps = [], args = [], data = [], **kwargs):
    kwargs["main"] = "pylint_test_wrapper.py"
    native.py_test(
        name = name,
        srcs = ["//bazel/workspace/tools/pylint:pylint_test_wrapper.py"] + srcs,
        args = ["--pylint-rcfile=$(location //bazel/workspace/tools/pylint:.pylintrc)"] + args + ["$(location :%s)" % x for x in srcs],
        python_version = "PY3",
        srcs_version = "PY3",
        deps = deps + [
            requirement("pytest"),
            requirement("pytest-pylint"),
        ],
        data = [
            "//bazel/workspace/tools/pylint:.pylintrc",
        ] + data,
        **kwargs
    )
