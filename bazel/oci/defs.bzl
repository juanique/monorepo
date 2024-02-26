load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("@rules_oci//oci:defs.bzl", "oci_image")
load("@aspect_bazel_lib//lib:tar.bzl", "tar")

def image(name, binary = None, base = "@distroless_base", **kwargs):
    tars = []

    if binary:
        entrypoint_name = "_" + name + ".entrypoint"
        _oci_entrypoint(
            name = entrypoint_name,
            binary = binary,
        )

        bin_tar_name = "_" + name + ".bin_tar"
        tar(
            name = bin_tar_name,
            srcs = [binary],
        )
        tars.append(bin_tar_name)

        entrypoint_tar_nane = "_" + name + ".entrypoint_tar"
        pkg_tar(
            name = entrypoint_tar_nane,
            srcs = [entrypoint_name],
            package_dir = "usr/local/bin",
        )

        tars.append(entrypoint_tar_nane)
        kwargs["entrypoint"] = ["/usr/local/bin/" + entrypoint_name + ".sh"]

    oci_image(
        name = name,
        base = base,
        tars = tars,
        **kwargs
    )

    loader_name = name + ".loader"
    oci_image_loader(
        name = loader_name,
        image = name,
        repo_tag = name + ":latest",
    )

def _oci_entrypoint_impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.name + ".sh")

    script = """#!/usr/bin/env bash
exec env --chdir /{chdir} RUNFILES_DIR=.. {bin_path} "$@"
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

def oci_image_loader_impl(ctx):
    """Implementation of oci_image_loader rule.

    Args:
      ctx: the rule context.

    Returns:
      DefaultInfo with executable that loads the image.
    """

    repo_tags = []
    repo_tags.append(ctx.label.package + "/" + ctx.attr.repo_tag)

    script = """#!/bin/bash
    ./{} {} {} "$@"
    """.format(
        ctx.executable._loader_bin.short_path,
        ctx.file.image.short_path,
        " ".join(repo_tags),
    )

    output = ctx.actions.declare_file(ctx.label.name + ".sh")
    ctx.actions.write(
        output = output,
        content = script,
        is_executable = True,
    )

    shaoutput = ctx.actions.declare_file(ctx.label.name + ".sha256")
    ctx.actions.run_shell(
        outputs = [shaoutput],
        inputs = [ctx.file.image, ctx.executable._loader_bin],
        command = """#!/bin/bash
{tool} {image} --only-get-image-id > {output}""".format(
            tool = ctx.executable._loader_bin.path,
            image = ctx.file.image.path,
            output = shaoutput.path,
        ),
    )

    runfiles = ctx.runfiles(files = [ctx.file.image])
    runfiles = runfiles.merge(ctx.attr.image[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge(ctx.attr._loader_bin[DefaultInfo].default_runfiles)

    return [
        DefaultInfo(files = depset([output, shaoutput]), runfiles = runfiles, executable = output),
    ]

oci_image_loader = rule(
    implementation = oci_image_loader_impl,
    attrs = {
        "image": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "Label of a directory containing an OCI layout, e.g. `oci_image`",
        ),
        "repo_tag": attr.string(
            mandatory = True,
            doc = "Tags to set to the image, will be prepended with the package name",
        ),
        "_loader_bin": attr.label(
            default = "//bazel/oci/loader",
            allow_single_file = True,
            executable = True,
            cfg = "target",
            doc = "Binary tool that can take in a directory containing an OCI layout and loade it.",
        ),
    },
    executable = True,
)
