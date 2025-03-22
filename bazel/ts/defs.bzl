load("@aspect_rules_swc//swc:defs.bzl", "swc")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@bazel_skylib//lib:partial.bzl", "partial")
load("//bazel/js:js.bzl", "js_binary")

def ts_binary(name, srcs = [], deps = [], entry_point = "", **kwargs):
    for src in srcs:
        if src in ["main.ts", "main.tsx", "main.js"]:
            entry_point = src
            break

    if not entry_point:
        fail("Missing main.ts, main.tsx or main.js in srcs for binary")

    lib_name = "_" + name + ".lib"
    ts_library(
        name = lib_name,
        srcs = srcs,
        deps = deps,
    )

    if entry_point.endswith(".ts"):
        entry_point = entry_point[:-3] + ".js"
    if entry_point.endswith(".tsx"):
        entry_point = entry_point[:-4] + ".js"

    js_binary(
        name = "main",
        data = [":" + lib_name],
        entry_point = entry_point,
    )

def ts_library(name, srcs = [], deps = [], **kwargs):
    # Not sure if there's any harm in adding this to all ts_library, in particular web targets.
    deps = list(deps)
    if "//:node_modules/@types/node" not in deps:
        deps.append("//:node_modules/@types/node")

    ts_project(
        name = name,
        srcs = srcs,
        deps = deps,
        declaration = True,
        transpiler = partial.make(
            swc,
            source_maps = "true",
            swcrc = "//:.swcrc",
        ),
        tsconfig = "//:tsconfig",
        **kwargs
    )
