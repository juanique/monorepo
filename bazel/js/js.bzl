load("@aspect_rules_js//js:defs.bzl", _js_binary = "js_binary", _js_library = "js_library")

def js_binary(name, data = [], srcs = [], deps = [], node_options = [], entry_point = None, **kwargs):
    for src in srcs:
        if src in ["main.ts", "main.tsx", "main.js"]:
            entry_point = src
            break

    if not entry_point:
        fail("Missing main.ts, main.tsx or main.js in srcs for binary")

    _js_binary(
        name = name,
        data = [
            "//bazel/js/node:launcher",
            "//bazel/js/node:loader",
        ] + data + srcs + deps,
        node_options = [
            "--import",
            "./$(rootpath //bazel/js/node:launcher)",
        ] + node_options,
        entry_point = entry_point,
        **kwargs
    )

js_library = _js_library
