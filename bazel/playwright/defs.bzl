load("@aspect_rules_swc//swc:defs.bzl", "swc")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@bazel_skylib//lib:partial.bzl", "partial")
load("@npm//:@playwright/test/package_json.bzl", "bin")

def _playwright_config_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.attr.name)
    ctx.actions.expand_template(
        template = ctx.file._config_tpl,
        output = output_file,
        substitutions = {},
    )
    return [DefaultInfo(files = depset([output_file]))]

playwright_config = rule(
    implementation = _playwright_config_impl,
    attrs = {
        "_config_tpl": attr.label(allow_single_file = True, default = "//bazel/playwright:playwright.config.tpl.ts"),
    },
)

def playwright_test(name, srcs, deps = [], tags = []):
    playwright_config(
        name = "playwright.config.js",
    )

    deps = list(deps)
    if not "//:node_modules/@playwright/test" in deps:
        deps.append("//:node_modules/@playwright/test")

    ts_project(
        name = name + ".lib",
        srcs = srcs,
        declaration = True,
        transpiler = partial.make(
            swc,
            source_maps = "true",
            swcrc = "//:.swcrc",
        ),
        tsconfig = "//:tsconfig",
        deps = deps,
    )

    bin.playwright_test(
        name = name,
        args = [
            "test",
            "--config=$(rootpath :playwright.config.js)",
        ],
        tags = tags,
        node_options = [
            "--import",
            "./$(rootpath //bazel/js/node:launcher)",
        ],
        data = [
            ":playwright.config.js",
            ":" + name + ".lib",
            "//third_party/binaries:chromium",
            "//bazel/js/node:launcher",
        ],
        env = {
            "CHROMIUM_BIN": "$(rootpath //third_party/binaries:chromium)",
        },
    )
