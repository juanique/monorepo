workspace(name = "monorepo")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

##################
# Golang support
http_archive(
    name = "io_bazel_rules_go",
    sha256 = "c6cf9da6668ac84c470c43cbfccb8fdc844ead2b5a8b918e2816d44f2986f644",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.55.0/rules_go-v0.55.0.zip",
        "https://github.com/bazelbuild/rules_go/releases/download/v0.55.0/rules_go-v0.55.0.zip",
    ],
)

load("@io_bazel_rules_go//go:deps.bzl", "go_download_sdk", "go_register_toolchains", "go_rules_dependencies")
load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies", "go_repository")
load("//:deps.bzl", "go_repositories")

# gazelle:repository_macro deps.bzl%go_repositories
go_repositories()

go_rules_dependencies()

go_register_toolchains(go_version = "1.23.10")

go_download_sdk(
    name = "go_sdk_amd64",
    goarch = "amd64",
    goos = "linux",
    version = "1.23.10",
)

go_download_sdk(
    name = "go_sdk_arm64",
    goarch = "arm64",
    goos = "linux",
    version = "1.23.10",
)

gazelle_dependencies(go_sdk = "go_sdk")


#########################
## rules_ python

http_archive(
    name = "rules_python",
    sha256 = "c6fb25d0ba0246f6d5bd820dd0b2e66b339ccc510242fd4956b9a639b548d113",
    strip_prefix = "rules_python-0.37.2",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.37.2/rules_python-0.37.2.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories", "python_register_toolchains")

py_repositories()


# pip dependencies
load("@rules_python//python:pip.bzl", "pip_parse")

python_register_toolchains(
    name = "python3_10",
    # Available versions are listed in @rules_python//python:versions.bzl.
    # We recommend using the same version your team is already standardized on.
    python_version = "3.10",
)

load("@python3_10//:defs.bzl", "interpreter")

pip_parse(
    name = "pip_deps",
    python_interpreter_target = interpreter,
    requirements_lock = "//:requirements_lock.txt",
)

# mypy:
pip_parse(
    name = "mypy_integration_pip_deps",
    python_interpreter_target = interpreter,
    requirements_lock = "//bazel/workspace:mypy_version.txt",
)

load("@mypy_integration_pip_deps//:requirements.bzl", install_mypy_deps = "install_deps")

install_mypy_deps()

# Load the starlark macro which will define your dependencies.
load("@pip_deps//:requirements.bzl", "install_deps")

# Call it to define repos for your requirements.
install_deps()

go_repository(
    name = "org_golang_google_genproto_googleapis_rpc",
    importpath = "google.golang.org/genproto/googleapis/rpc",
    sum = "h1:eSaPbMR4T7WfH9FvABk36NBMacoTUKdWCvV0dx+KfOg=",
    version = "v0.0.0-20230803162519-f966b187b2e5",
)

go_repository(
    name = "org_golang_google_grpc",
    build_file_proto_mode = "disable_global",
    importpath = "google.golang.org/grpc",
    sum = "h1:fPVVDxY9w++VjTZsYvXWqEf9Rqar/e+9zYfxKK+W+YU=",
    version = "v1.50.0",
)

go_repository(
    name = "org_golang_x_net",
    importpath = "golang.org/x/net",
    sum = "h1:BONx9s002vGdD9umnlX1Po8vOZmrgH34qlHcD1MfK14=",
    version = "v0.14.0",
)

go_repository(
    name = "org_golang_x_text",
    importpath = "golang.org/x/text",
    sum = "h1:k+n5B8goJNdU7hSvEtMUz3d1Q6D/XW4COJSJR6fN0mc=",
    version = "v0.12.0",
)






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
