from __future__ import print_function

import logging
import sys

import grpc
from examples.grpc.protos import helloworld_pb2
from examples.grpc.protos import helloworld_pb2_grpc


def run(name):
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(helloworld_pb2.HelloRequest(name=name))
    print("Greeter client received: " + response.message)


if __name__ == "__main__":
    logging.basicConfig()
    name = sys.argv[1] if len(sys.argv) > 1 else "there"
    run(name)
