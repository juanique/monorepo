import os

import docker

from bazel_tools.tools.python.runfiles import runfiles

DEFAULT_NETWORK = os.environ.get("TESTING_DOCKER_SERVICES_NETWORK") or "br0"


class DockerService:
    def __init__(
        self,
        docker_client: docker.DockerClient,
        image_name: str,
        image_tar: str,
        container_name: str,
        port: int,
        network: str = DEFAULT_NETWORK,
    ):
        self.docker_client = docker_client
        self.image_name = image_name
        self.image_tar = image_tar
        self.container_name = container_name
        self.port = port
        self.network = network
        self.stopping = False

    def start(self) -> None:
        """Stop or restart the docker container running the service."""

        self.stop()

        tar_image = runfiles.Create().Rlocation(self.image_tar)
        with open(tar_image, "rb") as tar_file:
            self.docker_client.images.load(tar_file)[0].tag(self.image_name, "latest")

        ports = None if self.network == "host" else {f"{self.port}": f"{self.port}"}
        self.docker_client.containers.run(
            self.image_name,
            name=self.container_name,
            ports=ports,
            network=self.network,
            detach=True,
        )

    def hostport(self) -> str:
        host = "localhost" if self.network in ["host", "bridge"] else self.container_name
        return f"{host}:{self.port}"

    def stop(self) -> None:
        """Stop the docker container running the service."""

        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            container.remove(force=True)
        except docker.errors.NotFound:
            pass
