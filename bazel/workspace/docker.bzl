load("@io_bazel_rules_docker//lang:image.bzl", "app_layer")
load("@io_bazel_rules_docker//container:container.bzl", "container_image")

def py_image(name, binary, port):
    """ Basic development docker image for python targets."""

    base_image_name = name + "_base_py_image"

    container_image(
        name = base_image_name,
        base = "@ubuntu//image",
        docker_run_flags = "-p127.0.0.1:" + port + ":" + port,
    )

    app_layer(
        name = name,
        base = ":" + base_image_name,
        binary = binary,
        create_empty_workspace_dir = True,
        entrypoint = ["/usr/bin/python3.10"],
    )
