import logging
import os
import threading
import time

import docker

from bazel_tools.tools.python.runfiles import runfiles

DEFAULT_NETWORK = os.environ.get("TESTING_DOCKER_SERVICES_NETWORK") or "br0"

logger = logging.getLogger(__name__)


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
        self.thread = None

    def _thread_func(self):
        self.stop()

        tar_image = runfiles.Create().Rlocation(self.image_tar)
        with open(tar_image, "rb") as tar_file:
            self.docker_client.images.load(tar_file)[0].tag(self.image_name, "latest")

        ports = None if self.network == "host" else {f"{self.port}": f"{self.port}"}
        container = self.docker_client.containers.run(
            self.image_name,
            name=self.container_name,
            ports=ports,
            network=self.network,
            detach=True,
        )

        for line in container.logs(stream=True):
            logger.info(line)

        logger.info("Ending deamon for %s", self.container_name)


    def start(self, wait_until_ready: bool = True) -> None:
        """Stop or restart the docker container running the service."""
        self.thread = threading.Thread(target=self._thread_func, daemon=True).start()

        if wait_until_ready:
            self.wait_until_ready()


    def host(self) -> str:
        return "localhost" if self.network in ["host", "bridge"] else self.container_name

    def hostport(self) -> str:
        return f"{self.host()}:{self.port}"

    def stop(self) -> None:
        """Stop the docker container running the service."""

        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            container.remove(force=True)
        except docker.errors.NotFound:
            pass

    def wait_until_ready(self) -> None:
        """Services can override this method to wait until they are ready."""
