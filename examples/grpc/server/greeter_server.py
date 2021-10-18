from concurrent import futures
from examples.grpc.protos import helloworld_pb2
from examples.grpc.protos import helloworld_pb2_grpc
from grpc_reflection.v1alpha import reflection
import grpc
import logging
import sys


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, req, context):
        logging.info("Got request %s", req)
        return helloworld_pb2.HelloReply(message="Hello %s!" % req.name)


def serve():
    port = 50051
    logging.info(f"Server starting at port {port}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    SERVICE_NAMES = (
        helloworld_pb2.DESCRIPTOR.services_by_name["Greeter"].full_name,
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
