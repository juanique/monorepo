FROM gcr.io/flame-public/buildbuddy-ci-runner:latest

RUN mkdir -p /github/home
ENV HOME=/github/home

ENV USE_BAZEL_VERSION=4.2.1
RUN apt-get update && apt-get install -y build-essential python3-distutils python3-dev python3-apt

# Pre-install bazel 4.2.1 to avoid bazelisk downloading & installing bazel on every
# CI run, at least for CI runs on the BuildBuddy repo itself.
RUN bazelisk version

RUN rm -rf /workdir
WORKDIR /workdir
RUN git clone https://github.com/juanique/monorepo.git
WORKDIR /workdir/monorepo
RUN git reset --hard 47aac21aac15610f62681f31012095294eb49c1b
RUN bazelisk clean
RUN bazelisk --output_user_root=/workdir/bazel-output-user-root --output_base=/workdir/bazel-output-base --install_base=/workdir/bazel-install-base build ... --disk_cache=/workdir/bazel-cache --repository_cache=/workdir/bazel-repository-cache --build_metadata=USER=docker_cache_build

## Hermetic python build requirements.

RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
RUN apt-get install -y libffi-dev