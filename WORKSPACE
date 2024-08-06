workspace(name = "monorepo")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

##################
# Golang support
http_archive(
    name = "io_bazel_rules_go",
    sha256 = "6734a719993b1ba4ebe9806e853864395a8d3968ad27f9dd759c196b3eb3abe8",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.45.1/rules_go-v0.45.1.zip",
        "https://github.com/bazelbuild/rules_go/releases/download/v0.45.1/rules_go-v0.45.1.zip",
    ],
)

http_archive(
    name = "bazel_gazelle",
    sha256 = "32938bda16e6700063035479063d9d24c60eda8d79fd4739563f50d331cb3209",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-gazelle/releases/download/v0.35.0/bazel-gazelle-v0.35.0.tar.gz",
        "https://github.com/bazelbuild/bazel-gazelle/releases/download/v0.35.0/bazel-gazelle-v0.35.0.tar.gz",
    ],
)

load("@io_bazel_rules_go//go:deps.bzl", "go_download_sdk", "go_register_toolchains", "go_rules_dependencies")
load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies", "go_repository")
load("//:deps.bzl", "go_repositories")

# gazelle:repository_macro deps.bzl%go_repositories
go_repositories()

go_rules_dependencies()

go_register_toolchains(go_version = "1.21.6")

go_download_sdk(
    name = "go_sdk_amd64",
    goarch = "amd64",
    goos = "linux",
    version = "1.21.6",
)

go_download_sdk(
    name = "go_sdk_arm64",
    goarch = "arm64",
    goos = "linux",
    version = "1.21.6",
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
    sha256 = "c68bdc4fbec25de5b5493b8819cfc877c4ea299c0dcb15c244c5a00208cde311",
    strip_prefix = "rules_python-0.31.0",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.31.0/rules_python-0.31.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories", "python_register_toolchains")

py_repositories()

http_archive(
    name = "rules_python_gazelle_plugin",
    sha256 = "d71d2c67e0bce986e1c5a7731b4693226867c45bfe0b7c5e0067228a536fc580",
    strip_prefix = "rules_python-0.29.0/gazelle",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.29.0/rules_python-0.29.0.tar.gz",
)

# To compile the rules_python gazelle extension from source,
# we must fetch some third-party go dependencies that it uses.

load("@rules_python_gazelle_plugin//:deps.bzl", _py_gazelle_deps = "gazelle_deps")

_py_gazelle_deps()

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

http_archive(
    name = "com_google_protobuf",
    sha256 = "c2c71ebc90af9796e8834f65093f2fab88b0a82b2a3e805b34842645a2afc4b0",
    strip_prefix = "protobuf-26.0",
    urls = ["https://github.com/protocolbuffers/protobuf/archive/refs/tags/v26.0.zip"],
)

http_archive(
    name = "rules_proto",
    sha256 = "dc3fb206a2cb3441b485eb1e423165b231235a1ea9b031b4433cf7bc1fa460dd",
    strip_prefix = "rules_proto-5.3.0-21.7",
    urls = [
        "https://github.com/bazelbuild/rules_proto/archive/refs/tags/5.3.0-21.7.tar.gz",
    ],
)

load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")

rules_proto_dependencies()

rules_proto_toolchains()

# grpc
http_archive(
    name = "com_github_grpc_grpc",
    patch_args = ["-p1"],
    patches = ["//bazel/patches:grpc.patch"],
    sha256 = "c9f9ae6e4d6f40464ee9958be4068087881ed6aa37e30d0e64d40ed7be39dd01",
    strip_prefix = "grpc-1.62.1",
    urls = ["https://github.com/grpc/grpc/archive/refs/tags/v1.62.1.tar.gz"],
)

load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")

grpc_deps(
    python_headers = "@python3_10//:python_headers",
)

load("@com_github_grpc_grpc//bazel:grpc_extra_deps.bzl", "grpc_extra_deps")

grpc_extra_deps()

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

##############
# Uber zig GCC toolchain
http_archive(
    name = "musl_toolchains",
    sha256 = "1e6cf99f35277dbb9c3b341a9986d0f33cf70e0cc76a58f062d2d9b7ab56eeeb",
    url = "https://github.com/bazel-contrib/musl-toolchain/releases/download/v0.1.17/musl_toolchain-v0.1.17.tar.gz",
)

load("@musl_toolchains//:repositories.bzl", "load_musl_toolchains")

load_musl_toolchains()

load("@musl_toolchains//:toolchains.bzl", "register_musl_toolchains")

register_musl_toolchains()

###############################
## Buildifier
http_archive(
    name = "buildifier_prebuilt",
    sha256 = "41d57362ee8f351b10d9313239bb4cbc6152fdc04aa86e63007a1b843ad33f4d",
    strip_prefix = "buildifier-prebuilt-6.1.2.1",
    urls = [
        "http://github.com/keith/buildifier-prebuilt/archive/6.1.2.1.tar.gz",
    ],
)

load("@buildifier_prebuilt//:deps.bzl", "buildifier_prebuilt_deps")

buildifier_prebuilt_deps()

load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")

bazel_skylib_workspace()

load("@buildifier_prebuilt//:defs.bzl", "buildifier_prebuilt_register_toolchains")

buildifier_prebuilt_register_toolchains()

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

############
# Rules foreign

git_repository(
    name = "rules_foreign_cc",
    commit = "7b673547a3b51febb4e67642bf0cc30c3ba09453",
    remote = "https://github.com/bazelbuild/rules_foreign_cc.git",
)

load("@rules_foreign_cc//foreign_cc:repositories.bzl", "rules_foreign_cc_dependencies")

# This sets up some common toolchains for building targets. For more details, please see
# https://bazelbuild.github.io/rules_foreign_cc/0.9.0/flatten.html#rules_foreign_cc_dependencies
rules_foreign_cc_dependencies()

############
# rules perl

http_archive(
    name = "rules_perl",
    sha256 = "7c35dd1f37c280b8a78bd6815b1b62ab2043a566396b0168ec8e91aa46d88fc3",
    strip_prefix = "rules_perl-0.2.3",
    urls = [
        "https://github.com/bazelbuild/rules_perl/archive/refs/tags/0.2.3.tar.gz",
    ],
)

load("@rules_perl//perl:deps.bzl", "perl_register_toolchains", "perl_rules_dependencies")

perl_rules_dependencies()

perl_register_toolchains()

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
# Rules apko

http_archive(
    name = "rules_apko",
    sha256 = "0c1152e23c72ebf9ffac1921e395ad6a5501e72ded4ce505a5e05161e1f0793d",
    strip_prefix = "rules_apko-1.2.3",
    url = "https://github.com/chainguard-dev/rules_apko/releases/download/v1.2.3/rules_apko-v1.2.3.tar.gz",
)

load("@rules_apko//apko:repositories.bzl", "apko_register_toolchains", "rules_apko_dependencies")

rules_apko_dependencies()

apko_register_toolchains(name = "apko")

load("@rules_apko//apko:translate_lock.bzl", "translate_apko_lock")

translate_apko_lock(
    name = "apko_wolfi_base",
    lock = "@//base_images/apko/wolfi-base:apko.lock.json",
)

load("@apko_wolfi_base//:repositories.bzl", "apko_repositories")

apko_repositories()

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
