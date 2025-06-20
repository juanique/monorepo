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

###########
# Aspect bazel lib

http_archive(
    name = "aspect_bazel_lib",
    sha256 = "c780120ab99a4ca9daac69911eb06434b297214743ee7e0a1f1298353ef686db",
    strip_prefix = "bazel-lib-2.7.9",
    url = "https://github.com/aspect-build/bazel-lib/releases/download/v2.7.9/bazel-lib-v2.7.9.tar.gz",
)

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


# mypy integration
http_archive(
    name = "mypy_integration",
    patch_args = ["-p1"],
    patches = ["//bazel/patches:mypy_integration.patch"],
    sha256 = "ffb9b0813e03f7147b1e182ab59cdd2e662c9566d91a4f97361e6db39185beaa",
    strip_prefix = "bazel-mypy-integration-863fde2e91d9b4e3d9ba1c6b3a84d0a1fee2d1b5",
    url = "https://github.com/bazel-contrib/bazel-mypy-integration/archive/863fde2e91d9b4e3d9ba1c6b3a84d0a1fee2d1b5.zip",
)

load(
    "@mypy_integration//repositories:repositories.bzl",
    mypy_integration_repositories = "repositories",
)

mypy_integration_repositories()

load("@mypy_integration//:config.bzl", "mypy_configuration")

mypy_configuration(
    mypy_exclude_list = "//:mypy.ignore",
)

http_archive(
    name = "io_buildbuddy_buildbuddy_toolchain",
    sha256 = "a2a5cccec251211e2221b1587af2ce43c36d32a42f5d881737db3b546a536510",
    strip_prefix = "buildbuddy-toolchain-829c8a574f706de5c96c54ca310f139f4acda7dd",
    urls = ["https://github.com/buildbuddy-io/buildbuddy-toolchain/archive/829c8a574f706de5c96c54ca310f139f4acda7dd.tar.gz"],
)

load("@io_buildbuddy_buildbuddy_toolchain//:deps.bzl", "buildbuddy_deps")

buildbuddy_deps()

load("@io_buildbuddy_buildbuddy_toolchain//:rules.bzl", "buildbuddy")

buildbuddy(name = "buildbuddy_toolchain")



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


###################
# rules OCI
http_archive(
    name = "rules_oci",
    sha256 = "46ce9edcff4d3d7b3a550774b82396c0fa619cc9ce9da00c1b09a08b45ea5a14",
    strip_prefix = "rules_oci-1.8.0",
    url = "https://github.com/bazel-contrib/rules_oci/releases/download/v1.8.0/rules_oci-v1.8.0.tar.gz",
)

load("@rules_oci//oci:dependencies.bzl", "rules_oci_dependencies")

rules_oci_dependencies()

load("@rules_oci//oci:repositories.bzl", "LATEST_CRANE_VERSION", "oci_register_toolchains")

oci_register_toolchains(
    name = "oci",
    crane_version = LATEST_CRANE_VERSION,
)

load("//third_party:oci_containers.bzl", "load_oci_images")

load_oci_images()

load("@aspect_bazel_lib//lib:repositories.bzl", "aspect_bazel_lib_dependencies", "aspect_bazel_lib_register_toolchains")

# Required bazel-lib dependencies

aspect_bazel_lib_dependencies()

# Register bazel-lib toolchains

aspect_bazel_lib_register_toolchains()

###############

############
# Rules distroless

http_archive(
    name = "rules_distroless",
    patch_args = ["-p1"],
    patches = ["//bazel/patches:rules_distroless.01.duplicated_deps.patch"],
    sha256 = "4c5e98aa15e3684b580ea2e2bc8b95bac6e23a26b25ec8747c39e74ced2305da",
    strip_prefix = "rules_distroless-0.3.4",
    url = "https://github.com/GoogleContainerTools/rules_distroless/releases/download/v0.3.4/rules_distroless-v0.3.4.tar.gz",
)

load("@rules_distroless//distroless:dependencies.bzl", "distroless_dependencies")

distroless_dependencies()

########## debian images
load("@rules_distroless//apt:index.bzl", "deb_index")

# bazel run @debian12//:lock
deb_index(
    name = "debian12",
    lock = "@//base_images/debian:debian12.lock.json",
    manifest = "//base_images/debian:debian12.yaml",
)

load("@debian12//:packages.bzl", "debian12_packages")

debian12_packages()
