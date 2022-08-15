def _copy_file_impl(ctx):
    output = ctx.actions.declare_file(ctx.attr.name)
    input = ctx.file.input

    ctx.actions.run_shell(
        arguments = [input.path, output.path],
        inputs = [input],
        outputs = [output],
        command = "cat $1 >> $2"
    )
    ctx.actions.run_shell(
        arguments = [input.path, output.path],
        inputs = [input],
        outputs = [output],
        command = "cat $1 >> $2"
    )
    return [DefaultInfo(files = depset([output]))]

copy_file = rule(
    implementation=_copy_file_impl,
    attrs = {
        "input": attr.label(allow_single_file = True, mandatory = True),
    },
)
