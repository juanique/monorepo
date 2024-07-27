"""A module defining the third party dependency SDL2"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def sdl2_repositories():
    http_archive(
        name = "sdl2",
        build_file = "//third_party/sdl2:BUILD.sdl2.bazel",
        sha256 = "be3ca88f8c362704627a0bc5406edb2cd6cc6ba463596d81ebb7c2f18763d3bf",
        strip_prefix = "SDL-release-2.30.5",
        urls = ["https://github.com/libsdl-org/SDL/archive/refs/tags/release-2.30.5.tar.gz"],
    )
