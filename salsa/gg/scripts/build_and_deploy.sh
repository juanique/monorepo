bazel build //gg:gg_cli.par
rm -f ~/bin/gg
cp bazel-bin/gg/gg_cli.par ~/bin/gg
