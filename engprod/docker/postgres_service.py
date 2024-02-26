import time
import psycopg2
import docker
import logging

from salsa.docker.testing.docker_service import DockerService

logger = logging.getLogger(__name__)


class PostgresService(DockerService):
    def __init__(self, docker_client: docker.DockerClient):
        super().__init__(
            docker_client,
            image_name="engprod/docker/postgres_image",
            loader_target="//engprod/docker:postgres_image.loader",
            container_name="postgres",
            port=5432,
        )

    def connect(self) -> psycopg2.extensions.connection:
        """Connect with retries."""

        attempts = 0
        last_error = Exception("Unknown error")
        while attempts < 30:
            try:
                return psycopg2.connect(
                    host=self.host(),
                    database="postgres",
                    user="postgres",
                    password="postgres",
                    connect_timeout=30,
                )
            except psycopg2.OperationalError as error:
                time.sleep(1)
                logger.info("Waiting for postgres: %s", error)
                last_error = error

        raise last_error

    def wait_until_ready(self) -> None:
        """When we can establish a connection, the service is ready."""
        conn = self.connect()
        conn.close()
