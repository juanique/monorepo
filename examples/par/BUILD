load("@subpar//:subpar.bzl", "par_binary")

py_library(
    name = "my_lib",
    srcs = ["my_lib.py"])

par_binary(
    name = "my_binary",
    imports = [""],
    srcs = ["my_binary.py"],
    deps = [":my_lib"])
