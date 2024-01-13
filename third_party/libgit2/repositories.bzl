load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def libgit2_repositories():
    http_archive(
        name = "libgit2",
        build_file = "//third_party/libgit2:BUILD.libgit2.bazel",
        sha256 = "adf17310b590e6e7618f070c742b5ee028aeeed2c60099bc4190c386b5060de1",
        strip_prefix = "libgit2-0.27.9/",
        url = "https://github.com/libgit2/libgit2/archive/v0.27.9.tar.gz",
    )
