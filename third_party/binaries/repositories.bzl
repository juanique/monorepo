load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

NATIVE_BINARY_BUILD_TPL = """
load("@bazel_skylib//rules:native_binary.bzl", "native_binary")
package(default_visibility = ["//visibility:public"])

filegroup(
    name = "all_files",
    srcs = glob(["**/*"]),
)
native_binary(
    name = "{name}",
    src = "{binary}",
    out = "{binary}",
    data = [":all_files"],
)
"""

def binary_repositories():
    http_archive(
        name = "docker",
        sha256 = "23db817b99aac6d5d7fcb1f706e50b5a412d78a9438975d6b4a54c58dc409bfb",
        strip_prefix = "docker",
        url = "https://download.docker.com/linux/static/stable/x86_64/docker-25.0.4.tgz",
        build_file = "//third_party/binaries:BUILD.docker.bazel",
    )

    http_archive(
        name = "chromium_linux_amd64",
        url = "https://playwright.azureedge.net/builds/chromium/1129/chromium-linux.zip",
        sha256 = "e6091f35f81cfbdf4fd3eb4f3f7916e841d43582f113f39f6e0d0c253485e56a",
        build_file_content = NATIVE_BINARY_BUILD_TPL.format(
            name = "chromium-bin",
            binary = "chrome-linux/chrome",
        ),
    )

    http_archive(
        name = "chromium_macos_arm64",
        url = "https://playwright.azureedge.net/builds/chromium/1129/chromium-mac-arm64.zip",
        sha256 = "59d179d0ad9ad792e51db81aef2d7bcc164e6f5df434c081888fbbeb4568bd0e",
        build_file_content = NATIVE_BINARY_BUILD_TPL.format(
            name = "chromium-bin",
            binary = "chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        ),
    )
