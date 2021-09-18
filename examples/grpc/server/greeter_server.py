from concurrent import futures
from examples.grpc.protos import helloworld_pb2
from examples.grpc.protos import helloworld_pb2_grpc
import grpc
import logging
import sys

print(helloworld_pb2)
print(repr(sys.version_info))


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, req, context):
        return helloworld_pb2.HelloReply(message="Hello %s!" % req.name)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
