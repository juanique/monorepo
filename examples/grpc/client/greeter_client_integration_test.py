import logging
import unittest
import docker

from salsa.docker.testing.docker_service import DockerService
from examples.grpc.client.greeter_client import GreeterClient

logger = logging.getLogger(__name__)


class TestGreeterClient(unittest.TestCase):
    def setUp(self) -> None:
        self.docker_client = docker.from_env()
        self.service = DockerService(
            self.docker_client,
            image_name="bazel/examples/grpc/server",
            image_tar="monorepo/examples/grpc/server/greeter_server_docker.tar",
            container_name="greeter_server",
            port=50051,
        )
        self.service.start()

    def tearDown(self) -> None:
        self.service.stop()
        self.docker_client.close()

    def test_hello(self) -> None:
        client = GreeterClient(self.service.hostport())
        self.assertEqual("Hello Juan!", client.say_hello("Juan"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
