import unittest
import docker

from engprod.docker.postgres_service import PostgresService


class TestPostgresImage(unittest.TestCase):
    def setUp(self) -> None:
        self.docker_client = docker.from_env()
        self.postgres_service = PostgresService(self.docker_client)
        self.postgres_service.start()

    def tearDown(self) -> None:
        self.postgres_service.stop()
        self.docker_client.close()

    def test_postgres(self) -> None:
        conn = self.postgres_service.connect()

        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                db_version = cur.fetchone()

        conn.close()

        self.assertRegex(db_version[0], r"PostgreSQL 11.3")


if __name__ == "__main__":
    unittest.main()
