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
