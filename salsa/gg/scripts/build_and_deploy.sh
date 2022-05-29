bzl test //salsa/gg:gg_test
if [ $? -ne 0 ]
then
    exit 1
fi

bzl build //salsa/gg:gg_cli --build_python_zip
rm -f ~/bin/gg

echo '#!/usr/bin/env python' > ~/bin/gg
cat bazel-bin/salsa/gg/gg_cli.zip >> ~/bin/gg
chmod +x ~/bin/gg
