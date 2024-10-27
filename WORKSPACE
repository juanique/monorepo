workspace(name = "monorepo")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

###########
# Aspect bazel lib

http_archive(
    name = "aspect_bazel_lib",
    sha256 = "c780120ab99a4ca9daac69911eb06434b297214743ee7e0a1f1298353ef686db",
    strip_prefix = "bazel-lib-2.7.9",
    url = "https://github.com/aspect-build/bazel-lib/releases/download/v2.7.9/bazel-lib-v2.7.9.tar.gz",
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

##############
# Uber zig GCC toolchain

HERMETIC_CC_TOOLCHAIN_VERSION = "v3.0.1"

http_archive(
    name = "hermetic_cc_toolchain",
    sha256 = "3bc6ec127622fdceb4129cb06b6f7ab098c4d539124dde96a6318e7c32a53f7a",
    urls = [
        "https://mirror.bazel.build/github.com/uber/hermetic_cc_toolchain/releases/download/{0}/hermetic_cc_toolchain-{0}.tar.gz".format(HERMETIC_CC_TOOLCHAIN_VERSION),
        "https://github.com/uber/hermetic_cc_toolchain/releases/download/{0}/hermetic_cc_toolchain-{0}.tar.gz".format(HERMETIC_CC_TOOLCHAIN_VERSION),
    ],
)

load("@hermetic_cc_toolchain//toolchain:defs.bzl", zig_toolchains = "toolchains")

register_toolchains(
    "@zig_sdk//toolchain:linux_amd64_gnu.2.28",
    "@zig_sdk//toolchain:linux_arm64_gnu.2.28",
    "@zig_sdk//toolchain:darwin_amd64",
    "@zig_sdk//toolchain:darwin_arm64",
    "@zig_sdk//toolchain:windows_amd64",
    "@zig_sdk//toolchain:windows_arm64",
)

# Plain zig_toolchains() will pick reasonable defaults. See
# toolchain/defs.bzl:toolchains on how to change the Zig SDK version and
# download URL.
zig_toolchains()

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
