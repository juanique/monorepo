workspace(name = "monorepo")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

#########################
## rules_ python

http_archive(
    name = "rules_python",
    sha256 = "a644da969b6824cc87f8fe7b18101a8a6c57da5db39caa6566ec6109f37d2141",
    strip_prefix = "rules_python-0.20.0",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.20.0/rules_python-0.20.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories", "python_register_toolchains")

py_repositories()

# pip dependencies
load("@rules_python//python:pip.bzl", "pip_parse")

python_register_toolchains(
    name = "python3_9",
    # Available versions are listed in @rules_python//python:versions.bzl.
    # We recommend using the same version your team is already standardized on.
    python_version = "3.9",
)

load("@python3_9//:defs.bzl", "interpreter")

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


# Golang support
http_archive(
    name = "io_bazel_rules_go",
    sha256 = "8e968b5fcea1d2d64071872b12737bbb5514524ee5f0a4f54f5920266c261acb",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.28.0/rules_go-v0.28.0.zip",
        "https://github.com/bazelbuild/rules_go/releases/download/v0.28.0/rules_go-v0.28.0.zip",
    ],
)

http_archive(
    name = "bazel_gazelle",
    sha256 = "62ca106be173579c0a167deb23358fdfe71ffa1e4cfdddf5582af26520f1c66f",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-gazelle/releases/download/v0.23.0/bazel-gazelle-v0.23.0.tar.gz",
        "https://github.com/bazelbuild/bazel-gazelle/releases/download/v0.23.0/bazel-gazelle-v0.23.0.tar.gz",
    ],
)

load("@io_bazel_rules_go//go:deps.bzl", "go_register_toolchains", "go_rules_dependencies")
load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies", "go_repository")

go_rules_dependencies()

go_register_toolchains(go_version = "1.18")

gazelle_dependencies()

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
    tag = "v1.33.2",
)

go_repository(
    name = "org_golang_x_net",
    importpath = "golang.org/x/net",
    sum = "h1:oWX7TPOiFAMXLq8o0ikBYfCJVlRHBcsciT5bXOrH628=",
    version = "v0.0.0-20190311183353-d8887717615a",
)

go_repository(
    name = "org_golang_x_text",
    importpath = "golang.org/x/text",
    sum = "h1:g61tztE5qeGQ89tm6NTjjM9VPIm088od1l6aSorWRWg=",
    version = "v0.3.0",
)

http_archive(
    name = "com_google_protobuf",
    strip_prefix = "protobuf-24.0",
    urls = ["https://github.com/protocolbuffers/protobuf/archive/refs/tags/v24.0.zip"],
    sha256 = "974409b1d6eb2b6508fd26bea2f9b327a4480f122a6fdf38e485321549308121",
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
    sha256 = "8393767af531b2d0549a4c26cf8ba1f665b16c16fb6c9238a7755e45444881dd",
    patch_args = ["-p1"],
    patches = ["//bazel/patches:grpc.patch"],
    strip_prefix = "grpc-1.57.0",
    urls = ["https://github.com/grpc/grpc/archive/v1.57.0.tar.gz"],
)

load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")

grpc_deps(
    python_headers = "@python3_9//:python_headers",
)

load("@com_github_grpc_grpc//bazel:grpc_extra_deps.bzl", "grpc_extra_deps")

grpc_extra_deps()

# Docker
http_archive(
    name = "io_bazel_rules_docker",
    sha256 = "b1e80761a8a8243d03ebca8845e9cc1ba6c82ce7c5179ce2b295cd36f7e394bf",
    urls = ["https://github.com/bazelbuild/rules_docker/releases/download/v0.25.0/rules_docker-v0.25.0.tar.gz"],
)

load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)

container_repositories()

load("@io_bazel_rules_docker//repositories:deps.bzl", container_deps = "deps")

container_deps()

load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_pull",
)

container_pull(
    name = "java_base",
    # 'tag' is also supported, but digest is encouraged for reproducibility.
    digest = "sha256:deadbeef",
    registry = "gcr.io",
    repository = "distroless/java",
)

load(
    "@io_bazel_rules_docker//python3:image.bzl",
    _py_image_repos = "repositories",
)

_py_image_repos()

# mypy integration
http_archive(
    name = "mypy_integration",
    sha256 = "cf94c102fbaccb587eea8de5cf1cb7f55c5c74396a2468932c3a2a4df989aa1d",
    strip_prefix = "bazel-mypy-integration-0.4.0",
    url = "https://github.com/thundergolfer/bazel-mypy-integration/archive/refs/tags/0.4.0.tar.gz",
    patch_args = ["-p1"],
    patches = ["//bazel/patches:mypy_integration.patch"],
)

load(
    "@mypy_integration//repositories:repositories.bzl",
    mypy_integration_repositories = "repositories",
)

mypy_integration_repositories()

load("@mypy_integration//:config.bzl", "mypy_configuration")

# Optionally pass a MyPy config file, otherwise pass no argument.
mypy_configuration("//bazel/workspace:mypy.ini")

load("@mypy_integration//repositories:deps.bzl", mypy_integration_deps = "deps")

container_pull(
    name = "ubuntu",
    registry = "docker.io",
    repository = "juanzolotoochin/ubuntu-base",
    tag = "latest",
)

container_pull(
    name = "build",
    registry = "docker.io",
    repository = "juanzolotoochin/ubuntu-build",
    tag = "latest",
)

container_pull(
    name = "postgres",
    registry = "docker.io",
    repository = "postgres",
    tag = "11.3-alpine",
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
# Aspect GCC toolchain

http_archive(
	name = "aspect_gcc_toolchain",
	strip_prefix = "gcc-toolchain-0.4.2",
    sha256 = "3341394b1376fb96a87ac3ca01c582f7f18e7dc5e16e8cf40880a31dd7ac0e1e",
	type = "tar.gz",
	urls = [
		"https://github.com/aspect-build/gcc-toolchain/archive/refs/tags/0.4.2.tar.gz",
	],
)

load("@aspect_gcc_toolchain//toolchain:repositories.bzl", "gcc_toolchain_dependencies")

gcc_toolchain_dependencies()

load("@aspect_gcc_toolchain//toolchain:defs.bzl", "ARCHS", "gcc_register_toolchain")

gcc_register_toolchain(
	name = "gcc_toolchain_aarch64",
	target_arch = ARCHS.aarch64,
)

gcc_register_toolchain(
	name = "gcc_toolchain_x86",
	target_arch = ARCHS.x86_64,
)

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