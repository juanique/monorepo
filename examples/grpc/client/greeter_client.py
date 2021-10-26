import grpc
from examples.grpc.protos import helloworld_pb2
from examples.grpc.protos import helloworld_pb2_grpc


class GreeterClient:
    def __init__(self, address: str):
        self.address = address
        channel = grpc.insecure_channel(self.address)
        grpc.channel_ready_future(channel).result(timeout=20)
        self.stub = helloworld_pb2_grpc.GreeterStub(channel)

    def say_hello(self, name: str) -> str:
        response = self.stub.SayHello(helloworld_pb2.HelloRequest(name=name))
        return response.message
