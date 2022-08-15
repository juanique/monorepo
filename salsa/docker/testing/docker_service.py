import logging
import os
import threading
import time
from typing import Optional

import docker

from bazel_tools.tools.python.runfiles import runfiles

DEFAULT_NETWORK = os.environ.get("TESTING_DOCKER_SERVICES_NETWORK") or "bazel-dev-network"

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
        self.thread: Optional[threading.Thread] = None
        self.container = None

    def _thread_func(self) -> None:
        self.stop()

        tar_image = runfiles.Create().Rlocation(self.image_tar)
        with open(tar_image, "rb") as tar_file:
            self.docker_client.images.load(tar_file)[0].tag(self.image_name, "latest")

        ports = None if self.network == "host" else {f"{self.port}": f"{self.port}"}
        logger.info("Starting %s", self.container_name)
        container = self.docker_client.containers.run(
            self.image_name,
            name=self.container_name,
            ports=ports,
            network=self.network,
            detach=True,
        )

        for line in container.logs(stream=True):
            logger.info("%s - %s", self.container_name, line.decode("utf-8").strip())

        logger.info("Ending deamon for %s", self.container_name)

    def _get_container(self) -> Optional[docker.models.containers.Container]:
        try:
            return self.docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            return None

    def start(self, wait_until_ready: bool = True) -> None:
        """Stop or restart the docker container running the service."""
        self.thread = threading.Thread(target=self._thread_func, daemon=True)
        self.thread.start()

        container = self._get_container()

        while not container or container.status != "running":
            time.sleep(0.5)
            container = self._get_container()
            if not container:
                logging.info("Container %s is not created yet", self.container_name)
            else:
                logging.info("Container %s is %s", self.container_name, container.status)

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
