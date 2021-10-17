FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y software-properties-common gcc && \
    add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y python3.10 python3-distutils python3.10-pip python3-apt

### Hermetic python dependencies
RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
RUN apt-get install -y build-essential checkinstall
RUN apt-get install -y libffi-dev zlib1g-dev
RUN apt-get install -y python3.10-distutils
RUN apt-get install -y python3.10-dev

### Git is used to download golang dependencies
RUN apt-get install -y git-all

## Install Bazel
RUN apt-get -y install wget
WORKDIR /workdir/setup
RUN wget https://github.com/bazelbuild/bazelisk/releases/download/v1.10.1/bazelisk-linux-amd64
RUN chmod +x ./bazelisk-linux-amd64
RUN ln -s /workdir/setup/bazelisk-linux-amd64 /usr/bin/bazelisk
RUN ln -s /usr/bin/python3.10 /usr/bin/python

WORKDIR /workdir

ENV USE_BAZEL_VERSION=4.2.1