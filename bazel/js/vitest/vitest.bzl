"Wrapper around vitest_test"

load("@npm//:vitest/package_json.bzl", "bin")

def vitest_test(name, srcs = [], deps = [], data = [], dom = False, **kwargs):
    config = "//bazel/js/vitest:vitest_config"
    if dom:
        config = "//bazel/js/vitest:vitest_component_config"

    extra_test_deps = [config, "//bazel/js/vitest:vitest_setup"]

    if dom:
        extra_test_deps.append("//:node_modules/jsdom")
        extra_test_deps.append("//:node_modules/@testing-library/jest-dom")

    bin.vitest_test(
        name = name,
        args = [
            "run",
            "--config",
            "$(rootpath " + config + ")",
        ],
        data = srcs + data + deps + extra_test_deps,
        **kwargs
    )
