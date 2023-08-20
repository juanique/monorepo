bazel test //salsa/gg:gg_test
if [ $? -ne 0 ]
then
    exit 1
fi

bazel build //salsa/gg:gg_executable

rm -f ~/bin/gg_dev
cp bazel-bin/salsa/gg/gg_executable ~/bin/gg_dev
