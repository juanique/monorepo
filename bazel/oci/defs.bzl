load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("@rules_oci//oci:defs.bzl", "oci_image")

def image(name, binary, base = "@distroless_base"):
    tars = []

    bin_tar_name = "_" + name + ".bin_tar"
    pkg_tar(
        name = bin_tar_name,
        srcs = [binary],
        package_dir = "usr/local/bin",
    )
    tars.append(bin_tar_name)

    entrypoint_name = "_" + name + ".entrypoint"
    _oci_entrypoint(
        name = entrypoint_name,
        binary = binary,
    )

    oci_image(
        name = name,
        base = base,
        entrypoint = ["/usr/local/bin/" + entrypoint_name],
        tars = [":" + bin_tar_name],
    )

def _oci_entrypoint_impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.name + ".sh")

    script = """#!/usr/bin/env bash
exec env --chdir /usr/local/bin/{chdir} RUNFILES_DIR=.. {bin_path} "$@"
""".format(
        chdir = ctx.executable.binary.short_path + ".runfiles/monorepo",
        bin_path = ctx.executable.binary.short_path,
    )

    ctx.actions.write(out, script)
    return DefaultInfo(files = depset([out]), executable = out)

_oci_entrypoint = rule(
    implementation = _oci_entrypoint_impl,
    attrs = {
        "binary": attr.label(mandatory = True, executable = True, cfg = "target"),
    },
    executable = True,
)
