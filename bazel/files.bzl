def copy_file(name, src, to):
    native.genrule(
        name = name,
        srcs = [src],
        outs = [to],
        cmd = "cp $(SRCS) $(OUTS)",
    )
