load("@aspect_rules_swc//swc:defs.bzl", "swc")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@bazel_skylib//lib:partial.bzl", "partial")
load("@npm//:@playwright/experimental-ct-react/package_json.bzl", ct_bin = "bin")
load("@npm//:@playwright/test/package_json.bzl", "bin")

def _playwright_config_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.attr.name)
    ctx.actions.expand_template(
        template = ctx.file.config_tpl,
        output = output_file,
        substitutions = {},
    )
    return [DefaultInfo(files = depset([output_file]))]

playwright_config = rule(
    implementation = _playwright_config_impl,
    attrs = {
        "config_tpl": attr.label(allow_single_file = True, default = "//bazel/playwright:playwright.config.tpl.ts"),
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

def playwright_component_test(name, srcs, deps = [], tags = [], data = []):
    # Note: not using `name` will lead to collisions when multiple tests in single package (if we want to support it)
    playwright_config(
        name = "playwright.config.js",
        config_tpl = "//bazel/playwright:playwright.component.config.tpl.ts",
    )

    # Note: can be better to either turn the config into a js_library or to make the playwright_config rule
    # output a JsInfo group with these deps, so the handling below can be cleaned up a bit

    deps = list(deps)
    if "//:node_modules/@playwright/experimental-ct-react" not in deps:
        deps.append("//:node_modules/@playwright/experimental-ct-react")

    # Note: playwright component testing does not work with pre-transpiled sources;
    # it must do its own transpilation in order to convert JSX component to their custom format
    # that feeds to `mount`. Pre-transpiling results in "object notation" for the component,
    # which is not supported currently.

    #ts_project(
    #    name = name + ".lib",
    #    srcs = srcs,
    #    declaration = True,
    #    transpiler = partial.make(
    #        swc,
    #        source_maps = "true",
    #        swcrc = "//:.swcrc",
    #    ),
    #    tsconfig = "//:tsconfig",
    #    deps = deps,
    #)

    ct_bin.playwright_test(
        name = name,
        args = [
            "test",
            "-c",
            "$(rootpath :playwright.config.js)",
        ],
        tags = tags,
        node_options = [
            "--import",
            "./$(rootpath //bazel/js/node:launcher)",
        ],
        data = srcs + deps + [
            ":playwright.config.js",
            #":" + name + ".lib",
            "//third_party/binaries:chromium",
            "//bazel/js/node:launcher",
        ] + data,
        env = {
            "CHROMIUM_BIN": "$(rootpath //third_party/binaries:chromium)",
        },
    )
