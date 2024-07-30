load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def alsa_repositories():
    http_archive(
        name = "alsa",
        urls = [
            "https://www.alsa-project.org/files/pub/lib/alsa-lib-1.2.12.tar.bz2",
        ],
        sha256 = "4868cd908627279da5a634f468701625be8cc251d84262c7e5b6a218391ad0d2",
        strip_prefix = "alsa-lib-1.2.12",
        build_file = Label("//third_party/alsa:BUILD.alsa.bazel"),
    )
