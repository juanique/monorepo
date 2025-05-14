load("@aspect_rules_swc//swc:defs.bzl", "swc")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@bazel_skylib//lib:partial.bzl", "partial")
load("//bazel/js:js.bzl", "js_binary")

def ts_binary(name, srcs = [], deps = [], data = [], entry_point = "", **kwargs):
    for src in srcs:
        print("checking src:", src)
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
        data = data,
    )

    if entry_point.endswith(".ts"):
        entry_point = entry_point[:-3] + ".js"
    if entry_point.endswith(".tsx"):
        entry_point = entry_point[:-4] + ".js"

    js_binary(
        name = name,
        srcs = [":" + lib_name],
        entry_point = entry_point,
    )

def ts_library(name, srcs = [], deps = [], **kwargs):
    if "//:node_modules/@types/node" not in deps:
        deps = list(deps)

        # Unsure if there's any issues with including the node stdlib types in all binary targets.
        # We do this because there's no explicit imports for these. People can just use `process`
        deps.append("//:node_modules/@types/node")

    ts_project(
        name = name,
        srcs = srcs,
        deps = deps + ["//:package_json"],
        declaration = True,
        transpiler = partial.make(
            swc,
            source_maps = "true",
            swcrc = "//:.swcrc",
        ),
        tsconfig = "//:tsconfig",
        **kwargs
    )
