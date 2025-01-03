load("@aspect_rules_swc//swc:defs.bzl", "swc")
load("@aspect_rules_ts//ts:defs.bzl", "ts_project")
load("@bazel_skylib//lib:partial.bzl", "partial")
load("//bazel/js:js.bzl", "js_binary")

def ts_binary(name, srcs = [], deps = [], **kwargs):
    if len(srcs) != 1:
        fail("ts_binary must have exactly one src which is the entrypoint")

    lib_name = "_" + name + ".lib"
    ts_library(
        name = lib_name,
        srcs = srcs,
        deps = deps,
    )

    entrypoint = srcs[0]
    if entrypoint.endswith(".ts"):
        entrypoint = entrypoint[:-3] + ".js"
    if entrypoint.endswith(".tsx"):
        entrypoint = entrypoint[:-4] + ".js"

    js_binary(
        name = "main",
        data = [":" + lib_name],
        entry_point = entrypoint,
    )

def ts_library(name, srcs = [], deps = [], **kwargs):
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
