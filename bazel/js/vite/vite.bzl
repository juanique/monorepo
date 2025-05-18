load("@aspect_rules_js//js:defs.bzl", "js_library", "js_run_binary", "js_run_devserver")
load("//:bazel/files.bzl", "copy_file")

def _vite_webapp_config_impl(ctx):
    package_name = ctx.label.package
    output_file = ctx.actions.declare_file(ctx.attr.name)
    ctx.actions.expand_template(
        template = ctx.file._config_tpl,
        output = output_file,
        substitutions = {
            "{PACKAGE}": package_name,
        },
    )
    return [DefaultInfo(files = depset([output_file]))]

_vite_webapp_config = rule(
    implementation = _vite_webapp_config_impl,
    attrs = {
        "_config_tpl": attr.label(allow_single_file = True, default = "//bazel/js/vite:vite.config.tpl.js"),
    },
)


def vite_webapp_config(name):
    _vite_webapp_config(
        name = "vite.config.js",
    )

    copy_file(
       name ="tailwind_config",
       src = "//bazel/js/vite:tailwind.config.cjs",
       to = "tailwind.config.js",
    )

    js_library(
        name = name,
        srcs = [
            "vite.config.js",
        ],
        data = [
            "tailwind.config.js",
        ],
        deps = [
            "//:node_modules/vite",
            "//:node_modules/@vitejs/plugin-react",
            "//:node_modules/@tailwindcss/vite",
        ],
    )

def vite_webapp(name, srcs = [], dev_env = {}):
    vite_webapp_config(
        name = name + ".vite.config",
    )

    js_run_binary(
        name = name + ".build",
        srcs = [
            ":" + name + ".vite.config",
        ] + srcs,
        # Uncomment to produce build.output.log. Note that this breaks dependencies that expect this rule to produce a single output.
        # stdout = "build.output.log",
        out_dirs = ["dist"],
        tool = "//:vite.bin",
        args = ["build", "--config", "$(rootpath :" + name + ".vite.config)"],
        include_transitive_sources = True,
        silent_on_success = False,
    )

    js_run_devserver(
        name = name,
        data = [
            ":" + name + ".vite.config",
        ] + srcs,
        tool = "//:vite.bin",
        args = ["--config", "$(rootpath :" + name + ".vite.config)"],
        include_transitive_sources = True,
        tags = ["ibazel_notify_changes"],
        env = dev_env,
    )
