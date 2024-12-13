load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def ffmpeg6_repositories():
    http_archive(
        name = "ffmpeg6",
        build_file = "//third_party/ffmpeg6:BUILD.ffmpeg6.bazel",
        sha256 = "2acb5738a1b4b262633ac2d646340403ae47120d9eb289ecad23fc90093c0d6c",
        strip_prefix = "FFmpeg-n6.0.1",
        urls = ["https://github.com/FFmpeg/FFmpeg/archive/refs/tags/n6.0.1.zip"],
    )
