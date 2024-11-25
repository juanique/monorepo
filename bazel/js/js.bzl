load("@aspect_rules_js//js:defs.bzl", _js_binary = "js_binary", _js_library = "js_library", _js_run_devserver = "js_run_devserver", "js_run_binary")

js_library = _js_library
js_run_devserver = _js_run_devserver

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

def _vite_webapp_config_impl(ctx):
    package_name = ctx.label.package
    output_file = ctx.actions.declare_file(ctx.attr.name)
    ctx.actions.expand_template(
        template = ctx.file._config_tpl,
        output = output_file,
        substitutions = {
            "{PACKAGE}": package_name,
        }
    )
    return [DefaultInfo(files = depset([output_file]))]


_vite_webapp_config = rule(
    implementation = _vite_webapp_config_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "_config_tpl": attr.label(allow_single_file = True, default = "//bazel/js/vite:vite.config.tpl.js"),
    },
)


def vite_webapp_config(name):
    _vite_webapp_config(
        name = "vite.config.js",
    )

    js_library(
        name = name,
        srcs = ["vite.config.js"],
        deps = [
            "//:node_modules/vite",
            "//:node_modules/@vitejs/plugin-react",
        ],
    )


def vite_webapp(name, srcs = []):
    native.filegroup(
        name = name + ".app_files",
        srcs = srcs,
    )

    vite_webapp_config(
        name = name + ".vite.config",
    )


    js_run_binary(
        name = name + ".build",
        srcs = [
            ":" + name + ".vite.config",
            ":" + name + ".app_files",
        ],
        stdout = "build.output.log",
        out_dirs = ["dist"],
        tool = "//:vite.bin",
        args = ["build", "--config", "$(rootpath :" + name + ".vite.config)"],
        include_transitive_sources = True,
        silent_on_success = False,
    )

    js_run_devserver(
        name = name,
        data= [
            ":" + name + ".vite.config",
            ":" + name + ".app_files",
        ],
        tool = "//:vite.bin",
        args = ["--config", "$(rootpath :" + name + ".vite.config)"],
        include_transitive_sources = True,
        tags = ["ibazel_notify_changes"],
    )
