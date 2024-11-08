load("@aspect_rules_js//js:defs.bzl", "js_binary")
load("@aspect_rules_swc//swc:defs.bzl", "swc")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@bazel_skylib//lib:partial.bzl", "partial")

def ts_binary(name, srcs = [], deps = [], **kwargs):
    if len(srcs) != 1:
        fail("ts_binary must have exactly one src which is the entrypoint")

    lib_name = "_" + name + ".lib"
    ts_project(
        name = lib_name,
        srcs = srcs,
        deps = deps,
        transpiler = partial.make(
            swc,
            source_maps = "true",
            swcrc = "//:.swcrc",
        ),
        tsconfig = {
            "compilerOptions": {
                "inlineSourceMap": True,
            },
        },
        **kwargs
    )

    entrypoint = srcs[0]
    if entrypoint.endswith(".ts"):
        entrypoint = entrypoint[:-3] + ".js"

    js_binary(
        name = "main",
        data = [":" + lib_name],
        entry_point = entrypoint,
    )
