FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y software-properties-common gcc && \
    add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y python3.10 python3.10-distutils python3.10-dev


### Python build dependencies
### TODO(juanique): Check if we need this.
RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
RUN apt-get install -y build-essential checkinstall
RUN apt-get install -y libffi-dev zlib1g-dev

### Git is used to download golang dependencies
RUN apt-get install -y git-all

## Install Bazel
RUN apt-get -y install wget
WORKDIR /workdir/setup
RUN wget https://github.com/bazelbuild/bazelisk/releases/download/v1.10.1/bazelisk-linux-amd64
RUN chmod +x ./bazelisk-linux-amd64
RUN ln -s /workdir/setup/bazelisk-linux-amd64 /usr/bin/bazelisk
RUN ln -s /usr/bin/python3.10 /usr/bin/python

## Needed for building grpc services for some reason
RUN apt-get update && apt-get install -y python3-distutils python3-dev

## Docker is used to build docker targets
RUN apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update
RUN apt-get install -y docker-ce docker-ce-cli containerd.io

## Install PIP for python 3.10
RUN apt-get install -y python3.10-venv
RUN /usr/bin/python3.10 -m ensurepip
RUN /usr/bin/python3.10 -m pip install --upgrade pip
RUN /usr/bin/python3.10 -m pip install debugpy==1.5.1

# Install netstat and ping to debug network connections
RUN apt-get install -y net-tools iputils-ping

# Required for postgres clients.
RUN apt-get update
RUN apt-get install -y postgresql postgresql-contrib libpq-dev

RUN apt-get update
RUN apt-get install -y openjdk-11-jdk --fix-missing




WORKDIR /workdir

ENV USE_BAZEL_VERSION=5.1.1
