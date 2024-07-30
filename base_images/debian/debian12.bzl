load("@rules_oci//oci:defs.bzl", "oci_image")
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")

LIBPANGO_PACKAGES = [
    "@debian12//fonts-freefont-ttf",
    "@debian12//fonts-noto",
    "@debian12//fonts-terminus",
    "@debian12//libcairo2",
    "@debian12//fontconfig",
    "@debian12//libpango-1.0-0",
    "@debian12//libharfbuzz0b",
    "@debian12//libpangoft2-1.0-0",
    "@debian12//libpangocairo-1.0-0",
]

def debian_image(name, debian_packages, tars = [], base = None, **kwargs):
    pkg_tar(
        name = name + ".linux_layers.tar",
        deps = select({
            "@platforms//cpu:arm64": [
                "%s/arm64" % package
                for package in debian_packages
            ],
            "@platforms//cpu:x86_64": [
                "%s/amd64" % package
                for package in debian_packages
            ],
        }),
    )

    oci_image(
        name = name,
        architecture = None if base else select({
            "@platforms//cpu:arm64": "arm64",
            "@platforms//cpu:x86_64": "amd64",
        }),
        os = None if base else "linux",
        base = base,
        tars = tars + [
            ":" + name + ".linux_layers.tar",
        ],
        **kwargs
    )
