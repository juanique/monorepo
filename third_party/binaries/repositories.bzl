load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def binary_repositories():
    http_archive(
        name = "docker",
        sha256 = "23db817b99aac6d5d7fcb1f706e50b5a412d78a9438975d6b4a54c58dc409bfb",
        strip_prefix = "docker",
        url = "https://download.docker.com/linux/static/stable/x86_64/docker-25.0.4.tgz",
        build_file = "//third_party/binaries:BUILD.docker.bazel",
    )
