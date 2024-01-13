#!/usr/bin/env bash
echo "$@" >> /tmp/gopackagesdriver.log

# We ignore requests to process ./... because it would build the entire monorepo.
TARGET="./..."
NEW_ARGS=()

for arg in "$@"; do
    if [ "$arg" != "$TARGET" ]; then
        NEW_ARGS+=("$arg")
    fi
done

export USE_BAZEL_VERSION=$(tail -n1 .bazelversion)
export GOPACKAGESDRIVER_BAZEL_BUILD_FLAGS="--bes_results_url= --bes_backend= --remote_cache= --workspace_status_command="
exec bazel run --tool_tag=gopackagesdriver -- @io_bazel_rules_go//go/tools/gopackagesdriver "${NEW_ARGS[@]}"
