load("@io_bazel_rules_go//go:def.bzl", "go_library")
load("@io_bazel_rules_go//proto:def.bzl", "go_proto_library")
load("@rules_proto//proto:defs.bzl", "proto_library")

# load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

proto_library(
    name = "helloworld_proto",
    srcs = ["helloworld.proto"],
    visibility = ["//visibility:public"],
)

py_proto_library(
    name = "helloworld_py_proto",
    visibility = ["//visibility:public"],
    deps = [":helloworld_proto"],
)

py_grpc_library(
    name = "helloworld_py_grpc",
    srcs = [":helloworld_proto"],
    visibility = ["//visibility:public"],
    deps = [":helloworld_py_proto"],
)

go_proto_library(
    name = "helloworld_go_proto",
    importpath = "example/helloworld/examples/grpc/protos",
    proto = ":helloworld_proto",
    visibility = ["//visibility:public"],
)

go_library(
    name = "protos",
    embed = [":helloworld_go_proto"],
    importpath = "example/helloworld/examples/grpc/protos",
    visibility = ["//visibility:public"],
)
