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
    py_debug(name = name + "_debug", og_name = name, **kwargs)

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

def py_debug(name, og_name, srcs, deps = [], args = [], data = [], **kwargs):
    wrapper_dep_name = og_name + "_debug_wrapper"
    wrapper_filename = wrapper_dep_name + ".py"

    py_debug_wrapper(name = wrapper_dep_name, out = wrapper_filename)

    native.py_binary(
        name = name,
        srcs = [wrapper_filename] + srcs,
        main = wrapper_filename,
        python_version = "PY3",
        srcs_version = "PY3",
        deps = deps + [
            requirement("pytest"),
            requirement("debugpy"),
            ":" + wrapper_dep_name,
        ],
        **kwargs
    )

def _py_debug_wrapper_impl(ctx):
    path = str(ctx.label)
    full_module = path.replace("//", "").replace("/", ".").replace(":", ".").replace("_debug_wrapper", "")

    ctx.actions.expand_template(
        template = ctx.file._template,
        output = ctx.outputs.out,
        substitutions = {
            "{FULL_MODULE}": full_module,
        },
    )
    return [PyInfo(transitive_sources = depset([ctx.outputs.out]))]

py_debug_wrapper = rule(
    implementation = _py_debug_wrapper_impl,
    attrs = {
        "_template": attr.label(
            default = Label("//bazel/workspace/tools/pydebug:pydebug_wrapper.py.template"),
            allow_single_file = True,
        ),
        "out": attr.output(mandatory = True),
    },
)

def pytest_test(name, srcs, deps = [], args = [], **kwargs):
    native.py_test(
        name = name,
        srcs = [
            "//bazel/workspace/tools/pytest:pytest_wrapper.py",
        ] + srcs,
        main = "//bazel/workspace/tools/pytest:pytest_wrapper.py",
        args = [
            "--capture=no",
        ] + args + ["$(location :%s)" % x for x in srcs],
        python_version = "PY3",
        srcs_version = "PY3",
        deps = deps + [
            requirement("pytest"),
        ],
        **kwargs
    )

def py_executable(name, binary):
    zip_target_name = binary.replace(":", "") + "_zip"
    native.filegroup(
        name = zip_target_name,
        srcs = [binary],
        output_group = "python_zip_file",
    )

    _py_executable_wrapper(name = name, binary = zip_target_name)

def _py_executable_wrapper_impl(ctx):
    output = ctx.actions.declare_file(ctx.attr.name)
    input = ctx.file.binary
    ctx.actions.run_shell(
        inputs = [input],
        outputs = [output],
        arguments = [input.path, output.path],
        command = "echo '#!/usr/bin/env python' >> $2 && cat $1 >> $2",
    )

    return [DefaultInfo(files = depset([output]))]

_py_executable_wrapper = rule(
    implementation = _py_executable_wrapper_impl,
    attrs = {
        "binary": attr.label(allow_single_file = True, mandatory = True),
    },
)
