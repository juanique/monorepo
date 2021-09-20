load("@subpar//:subpar.bzl", "par_binary")

py_library(
    name = "my_lib",
    srcs = ["my_lib.py"],
)

par_binary(
    name = "my_binary",
    srcs = ["my_binary.py"],
    imports = [""],
    deps = [":my_lib"],
)
