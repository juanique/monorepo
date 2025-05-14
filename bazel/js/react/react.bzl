load("//bazel/js/vite:vite.bzl", "vite_webapp")
load("//bazel/js:ts.bzl", "ts_binary")

def _react_boilerplate_impl(ctx):
    package_name = ctx.label.package
    index_html = ctx.actions.declare_file("index.html")
    ctx.actions.expand_template(
        template = ctx.file._index_html_tpl,
        output = index_html,
        substitutions = {
            "{PACKAGE}": package_name,
        },
    )

    main_tsx = ctx.actions.declare_file("main.tsx")
    ctx.actions.expand_template(
        template = ctx.file._main_tsx_tpl,
        output = main_tsx,
        substitutions = {
            "{PACKAGE}": package_name,
        },
    )

    return [DefaultInfo(files = depset([index_html, main_tsx]))]

react_boilerplate = rule(
    implementation = _react_boilerplate_impl,
    attrs = {
        "outs": attr.output_list(mandatory = True),
        "_index_html_tpl": attr.label(
            allow_single_file = True,
            default = "//bazel/js/react:index.tpl.html",
        ),
        "_main_tsx_tpl": attr.label(
            allow_single_file = True,
            default = "//bazel/js/react:main.tpl.tsx",
        ),
    },
)

def react_app(name, srcs = [], deps = [], data = []):
    # TODO(juan.munoz): Add optional index.html/main.tsx files instead of generating them always with
    # the boilerplate rule.
    react_deps = [
        "//:node_modules/@types/react",
        "//:node_modules/@types/react-dom",
        "//:node_modules/react",
        "//:node_modules/react-dom",
    ]

    deps = list(deps)
    for dep in react_deps:
        if dep not in deps:
            deps.append(dep)

    react_boilerplate(
        name = name + ".boilerplate",
        outs = ["index.html", "main.tsx"],
    )

    ts_binary(
        name = name + ".lib",
        srcs = srcs + ["main.tsx"],
        deps = deps,
        data = data,
    )

    vite_webapp(
        name = name,
        srcs = ["index.html", ":" + name + ".lib"],
    )
