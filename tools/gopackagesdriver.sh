#!/usr/bin/env bash
echo "$@" >> /tmp/gopackagesdriver.log

# To debug use a command like this:
# echo {} | ./tools/gopackagesdriver.sh file=examples/go/helloworld.go
#
# You can also inspect
# tail -f /tmp/gopackagesdriver.log

# We ignore requests to process ./... because it would build the entire monorepo.
TARGET="./..."
NEW_ARGS=()

for arg in "$@"; do
    if [ "$arg" != "$TARGET" ]; then
        NEW_ARGS+=("$arg")
    fi
done

export GOPACKAGESDRIVER_BAZEL_FLAGS="--output_base=$HOME/.cache/bazel/gopackagesdriver"
export USE_BAZEL_VERSION=$(tail -n1 .bazelversion)
export GOPACKAGESDRIVER_BAZEL_BUILD_FLAGS="--bes_results_url= --bes_backend= --remote_cache= --workspace_status_command="
exec bazel --output_base=$HOME/.cache/bazel/gopackagesdriver run --config=full_local --tool_tag=gopackagesdriver @io_bazel_rules_go//go/tools/gopackagesdriver "${NEW_ARGS[@]}"
