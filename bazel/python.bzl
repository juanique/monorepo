load("@pip_deps//:requirements.bzl", "requirement")

FIRECRACKER_EXEC_PROPERTIES = {
    # Tell BuildBuddy to run this test using a Firecracker microVM.
    "test.workload-isolation-type": "firecracker",
    # Tell BuildBuddy to ensure that the Docker daemon is started
    # inside the microVM before the test starts, so that we don't
    # have to worry about starting it ourselves.
    "test.init-dockerd": "true",
    # Tell BuildBuddy to preserve the microVM state across test runs.
    "test.recycle-runner": "true",
    "container-image": "docker://docker.io/juanzolotoochin/ubuntu-build@sha256:e40b6484a68eb805862dc1dd3a474aa355db4b8b9f393a5ae29ba5b908ea36eb",
}

def py_binary(name, srcs, **kwargs):
    """ Wrapper for py_binary rule that adds additional functionality.

    Two additional targets are added, one for .par target and one for mypy check
    test.

    Args:
     name: Name that will be used for the native py_binary target.
     **kwargs: All other target args.
    """

    if "main" not in kwargs:
        if len(srcs) == 1:
            kwargs["main"] = srcs[0]
        else:
            fail("Missing main attribute for multi srcs target.")

    native.py_binary(name = name, srcs = srcs, **kwargs)

    py_ruff_test(name = name + "_pylint", srcs = srcs)

def py_library(name, srcs, **kwargs):
    native.py_library(name = name, srcs = srcs, **kwargs)
    py_ruff_test(name = name + "_pylint", srcs = srcs)

def py_test(name, srcs, firecracker = False, **kwargs):
    if firecracker:
        native.py_test(
            name = name,
            exec_properties = FIRECRACKER_EXEC_PROPERTIES,
            srcs = srcs,
            **kwargs
        )
    else:
        native.py_test(
            name = name,
            srcs = srcs,
            **kwargs
        )
    py_ruff_test(name = name + "_pylint", srcs = srcs)
    py_debug(name = name + "_debug", srcs = srcs, og_name = name, **kwargs)

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
    full_module = path.replace("//", "").replace("/", ".").replace(":", ".").replace("_debug_wrapper", "").replace("@", "")

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

def _py_ruff_test_impl(ctx):
    file_list = " ".join([file.short_path for file in ctx.files.srcs])
    srcs_hash = hash(file_list)
    script = "{runner} {file_list}".format(runner = ctx.executable._ruff_runner.short_path, file_list = file_list)
    script_file = ctx.actions.declare_file("ruff_check_" + str(srcs_hash) + ".sh")
    ctx.actions.write(output = script_file, content = script)

    runfiles = ctx.runfiles(files = ctx.files.srcs)
    runfiles = runfiles.merge(ctx.attr._ruff_runner[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge(ctx.attr._config_file[DefaultInfo].default_runfiles)
    return DefaultInfo(files = depset([script_file]), executable = script_file, runfiles = runfiles)

py_ruff_test = rule(
    implementation = _py_ruff_test_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = True,
            mandatory = True,
            doc = "*.py files to check with ruff",
        ),
        "_ruff_runner": attr.label(
            default = "//bazel/workspace/tools/ruff",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "_config_file": attr.label(
            default = "//:pyproject.toml",
            allow_single_file = True,
        ),
    },
    doc = "Wrapper for running ruff checks on python files.",
    test = True,
)
