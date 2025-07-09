bazel test //salsa/gg:gg_test
if [ $? -ne 0 ]
then
    exit 1
fi

bazel build //salsa/gg:gg_cli --build_runfile_links

rm -f ~/bin/gg
rm -rf ~/bin/gg.runfiles

cp bazel-bin/salsa/gg/gg_cli ~/bin/gg
cp -rL bazel-bin/salsa/gg/gg_cli.runfiles ~/bin/gg.runfiles
