import sys
from salsa.cli_proxy.protos.cli_proxy_pb2 import CallCliCommandRequest, CallCliCommandResponse
from salsa.cli_proxy.protos.cli_proxy_pb2_grpc import CliProxyServicer
from salsa.cli_proxy.protos import cli_proxy_pb2_grpc
from salsa.cli_proxy.protos import cli_proxy_pb2
from grpc_reflection.v1alpha import reflection
from concurrent import futures
import grpc

import logging

from salsa.gg.gg_cli import get_cli

logger = logging.getLogger(__name__)


class CliServer(CliProxyServicer):
    def __init__(self):
        self.cli = get_cli()

    def CallCliCommand(self, req: CallCliCommandRequest) -> CallCliCommandResponse:
        return "hello"


def serve():
    port = 50051
    logger.info(f"Server starting at port {port}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cli_proxy_pb2_grpc.add_CliProxyServicer_to_server(CliServer(), server)
    SERVICE_NAMES = (
        cli_proxy_pb2.DESCRIPTOR.services_by_name["CliProxy"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        filemode="w",
        format="%(levelname)s %(asctime)s - %(message)s",
        level=logging.INFO,
    )

    serve()
