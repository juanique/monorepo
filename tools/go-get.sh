#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: go-get.sh <package>"
  exit 1
fi

package=$1

pushd $BUILD_WORKSPACE_DIRECTORY
bazel run @go_sdk//:bin/go -- get $package
bazel run //:gazelle-update-repos --remote_download_outputs=all
popd
