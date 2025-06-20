workspace(name = "monorepo")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")










###################
## ruff
http_archive(
    name = "ruff",
    build_file_content = """
load("@bazel_skylib//rules:native_binary.bzl", "native_binary")

package(default_visibility = ["//visibility:public"])

native_binary(
    name = "ruff-bin",
    src = "ruff",
    out = "ruff",
)
    """,
    sha256 = "bb8219885d858979270790d52932f53444006f36b2736d453ae590b833f00476",
    urls = ["https://github.com/astral-sh/ruff/releases/download/v0.0.285/ruff-x86_64-unknown-linux-gnu.tar.gz"],
)

###############
# Third party
load("//third_party:repositories.bzl", "third_party_repositories")

third_party_repositories()





###############

############
