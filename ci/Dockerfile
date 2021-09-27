FROM gcr.io/flame-public/buildbuddy-ci-runner:latest

ENV USE_BAZEL_VERSION=4.2.1
RUN apt-get update && apt-get install -y build-essential python3-distutils python3-dev python3-apt

# Pre-install bazel 4.2.1 to avoid bazelisk downloading & installing bazel on every
# CI run, at least for CI runs on the BuildBuddy repo itself.
RUN bazelisk version

WORKDIR /workdir
RUN echo "Clonning repo at c4ca218ab07104a343b19b6d816100e846751a7d"
RUN git clone https://github.com/juanique/monorepo.git
WORKDIR /workdir/monorepo
RUN bazelisk clean
RUN bazelisk build ... --disk_cache=./bazel-cache