"""A module defining the third party dependency OpenSSL"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def openssl_repositories():
    http_archive(
        name = "openssl",
        build_file = "//third_party/openssl:BUILD.openssl3.bazel",
        sha256 = "aa7d8d9bef71ad6525c55ba11e5f4397889ce49c2c9349dcea6d3e4f0b024a7a",
        strip_prefix = "openssl-3.0.5",
        urls = ["https://www.openssl.org/source/openssl-3.0.5.tar.gz"],
    )
