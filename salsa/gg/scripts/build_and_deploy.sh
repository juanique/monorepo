bzl test //salsa/gg:gg_test
if [ $? -ne 0 ]
then
    exit 1
fi

bzl build //salsa/gg:gg_cli --build_python_zip
rm -f ~/bin/gg

echo '#!/usr/bin/env python' > ~/bin/gg_dev
cat bazel-bin/salsa/gg/gg_cli.zip >> ~/bin/gg_dev
chmod +x ~/bin/gg
