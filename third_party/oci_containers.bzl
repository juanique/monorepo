# You can pull your base images using oci_pull like this:
load("@rules_oci//oci:pull.bzl", "oci_pull")

def load_oci_images():
    oci_pull(
        name = "distroless_base",
        digest = "sha256:ccaef5ee2f1850270d453fdf700a5392534f8d1a8ca2acda391fbb6a06b81c86",
        image = "gcr.io/distroless/base",
        platforms = [
            "linux/amd64",
            "linux/arm64",
        ],
    )

    # amd64
    oci_pull(
        name = "ubuntu22",
        digest = "sha256:b492494d8e0113c4ad3fe4528a4b5ff89faa5331f7d52c5c138196f69ce176a6",
        image = "index.docker.io/library/ubuntu",
    )

    oci_pull(
        name = "build",
        digest = "sha256:2a669a950ee7941bf0e308372aa9ab1a38dc5491f75e3d6acf7b5e941a3bc32f",
        image = "index.docker.io/juanzolotoochin/ubuntu-build",
    )

    oci_pull(
        name = "nvidia-cuda",
        digest = "sha256:fb0ac5fcdfdbc87368da7dcc3755717a288587e962e8399895f7f1e58bb7b3c4",
        image = "index.docker.io/nvidia/cuda",
    )
