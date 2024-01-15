"""A module defining the third party dependency libgit2"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def libgit2_repositories():
    http_archive(
        name = "libgit2",
        build_file = Label("//third_party/libgit2:BUILD.libgit2.bazel"),
        sha256 = "7074f1e2697992b82402501182db254fe62d64877b12f6e4c64656516f4cde88",
        strip_prefix = "libgit2-1.5.1",
        urls = [
            "https://github.com/libgit2/libgit2/archive/refs/tags/v1.5.1.tar.gz",
        ],
    )
