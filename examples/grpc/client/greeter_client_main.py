import logging
import sys

from examples.grpc.client.greeter_client import GreeterClient


if __name__ == "__main__":
    logging.basicConfig()
    name = sys.argv[1] if len(sys.argv) > 1 else "there"
    client = GreeterClient("localhost:50051")
    print(client.say_hello(name))
