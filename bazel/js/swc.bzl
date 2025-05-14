"Simple definitions for invoking SWC"

load("@aspect_rules_swc//swc:defs.bzl", _swc = "swc")
load("@bazel_skylib//lib:partial.bzl", "partial")

swc = partial.make(
    _swc,
    swcrc = "//bazel/js:.swcrc",
)
