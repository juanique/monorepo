FROM juanzolotoochin/ubuntu-build

RUN mkdir -p /github/home
ENV HOME=/github/home

# Pre-install to avoid bazelisk downloading & installing bazel on every
# CI run
RUN bazelisk version

RUN echo "SYNC AT 02eb1782d54e73fd8d2882b483d4fcce554c9ef2" > /dev/null
WORKDIR /workdir
RUN git clone https://github.com/juanique/monorepo.git
WORKDIR /workdir/monorepo
RUN git reset --hard 02eb1782d54e73fd8d2882b483d4fcce554c9ef2
RUN bazelisk --output_user_root=/workdir/bazel-output-user-root --output_base=/workdir/bazel-output-base --install_base=/workdir/bazel-install-base build ... --disk_cache=/workdir/bazel-cache --repository_cache=/workdir/bazel-repository-cache --build_metadata=USER=docker_cache_build