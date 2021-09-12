load("@pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "greeter_client",
    srcs = ["greeter_client.py"],
    deps = [
        requirement("grpcio"),
        "//examples/grpc/protos:helloworld_py_grpc",
        "//examples/grpc/protos:helloworld_py_proto",
    ],
)
