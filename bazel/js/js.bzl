load("@aspect_rules_js//js:defs.bzl", _js_binary = "js_binary", _js_library = "js_library", _js_run_devserver = "js_run_devserver")

def js_binary(data = [], node_options = [], **kwargs):
    _js_binary(
        data = [
            "//bazel/js/node:launcher",
            "//bazel/js/node:loader",
        ] + data,
        node_options = [
            "--import",
            "./$(rootpath //bazel/js/node:launcher)",
        ] + node_options,
        **kwargs
    )

js_library = _js_library
js_run_devserver = _js_run_devserver

def _vite_build_impl(ctx):
    output_dir = ctx.actions.declare_directory(ctx.attr.name)
    script = """!
{tool} build --config {config}
""".format(tool = ctx.executable.tool.path, config = ctx.file.config.path)
    ctx.actions.run_shell(
        inputs = [ctx.executable.tool, ctx.file.config] + ctx.files.data,
        outputs = [output_dir],
        command = script,
    )

    return [DefaultInfo(files = depset([output_dir]))]



vite_build = rule(
    implementation = _vite_build_impl,
    attrs = {
        "data": attr.label_list(allow_files = True),
        "config": attr.label(allow_single_file = True),
        "tool": attr.label(
            allow_files = True,
            default = "//:vite.build",
            executable = True,
            cfg = "exec",
        ),
    },
)
