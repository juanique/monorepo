import logging
import signal
import os
import threading
import time
from typing import Optional

import docker
import subprocess

from bazel_tools.tools.python.runfiles import runfiles

DEFAULT_NETWORK = os.environ.get("TESTING_DOCKER_SERVICES_NETWORK") or "host"

logger = logging.getLogger(__name__)


class DockerService:
    def __init__(
        self,
        docker_client: docker.DockerClient,
        image_name: str,
        container_name: str,
        port: int,
        image_tar: Optional[str] = None,
        loader_target: Optional[str] = None,
        network: str = DEFAULT_NETWORK,
    ):
        self.docker_client = docker_client
        self.image_name = image_name
        self.image_tar = image_tar
        self.loader_target = loader_target
        self.container_name = container_name
        self.port = port
        self.network = network
        self.stopping = False
        self.thread: Optional[threading.Thread] = None
        self.container = None

    def _load_from_tar(self) -> None:
        tar_image = runfiles.Create().Rlocation(self.image_tar)
        with open(tar_image, "rb") as tar_file:
            self.docker_client.images.load(tar_file)[0].tag(self.image_name, "latest")

    def _load_from_loader_bin(self) -> None:
        assert self.loader_target

        loader_bin = "monorepo/" + (
            self.loader_target.replace(
                "//",
                "",
            ).replace(":", "/")
            + ".sh"
        )
        bin_path = runfiles.Create().Rlocation(loader_bin)
        result = subprocess.run(
            [bin_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        if result.returncode != 0:
            raise ValueError("Failed to load image: %s", result.stdout)

    def _thread_func(self) -> None:
        self.stop()

        try:
            if self.image_tar:
                self._load_from_tar()
            elif self.loader_target:
                self._load_from_loader_bin()
            else:
                raise ValueError("missing loader")
        except Exception as e:
            print(e)
            # TODO: find a more elegant solution to handle this.
            os.kill(os.getpid(), signal.SIGINT)

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
        logger.info("Starting image %s", self.image_name)
        self.thread = threading.Thread(target=self._thread_func, daemon=True)
        self.thread.start()

        container = self._get_container()

        while not container or container.status != "running":
            time.sleep(0.5)
            alive = self.thread.is_alive()
            container = self._get_container()
            print(alive)
            if not alive:
                self.thread.join()
            if not container:
                logging.info("Container %s is not created yet", self.container_name)
            else:
                logging.info("Container %s is %s", self.container_name, container.status)

        logger.info("Container is created")
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
