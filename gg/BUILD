load("@pip_deps//:requirements.bzl", "requirement")
load("@subpar//:subpar.bzl", "par_binary")

py_library(
    name = "gg",
    srcs = ["gg.py"],
    deps = [
        requirement("rich"),
        requirement("GitPython"),
    ],
)

par_binary(
    name = "gg_cli",
    srcs = ["gg_cli.py"],
    imports = [""],
    deps = [
        ":gg",
        requirement("GitPython"),
        requirement("rich"),
        requirement("click"),
    ],
)


py_test(
    name = "gg_test",
    srcs = ["gg_test.py"],
    deps = [
        ":gg",
        requirement("GitPython"),
    ],
)

py_binary(
    name = "gg_example",
    srcs = ["gg_example.py"],
    deps = [
        ":gg",
        requirement("GitPython"),
    ],
)
