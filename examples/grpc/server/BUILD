load("@pip_deps//:requirements.bzl", "requirement")
load("@io_bazel_rules_docker//python:image.bzl", "py_image")

py_image(
    name = "greeter_server_docker",
    srcs = ["greeter_server.py"],
    main = "greeter_server.py",
    deps = [
        requirement("grpcio"),
        "//examples/grpc/protos:helloworld_py_grpc",
        "//examples/grpc/protos:helloworld_py_proto",
    ],
)

py_binary(
    name = "greeter_server",
    srcs = ["greeter_server.py"],
    deps = [
        requirement("grpcio"),
        "//examples/grpc/protos:helloworld_py_grpc",
        "//examples/grpc/protos:helloworld_py_proto",
    ],
)
