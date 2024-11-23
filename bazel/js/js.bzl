load("@aspect_rules_js//js:defs.bzl", _js_binary = "js_binary", _js_library = "js_library", _js_run_devserver = "js_run_devserver")

def js_binary(data = [], node_options = [], **kwargs):
    _js_binary(
        data = [
            "//bazel/js/node:js_binary_init",
        ] + data,
        node_options = [
            "-r",
            "./$(rootpath //bazel/js/node:js_binary_init)",
        ] + node_options,
        **kwargs
    )

js_library = _js_library
js_run_devserver = _js_run_devserver
