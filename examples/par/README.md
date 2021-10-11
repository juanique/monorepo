### Python self contained executables

`.par` is no longer maintained by Google. In order to create a self contained python zip executable run:

```
bazel build //examples/par:my_binary --build_python_zip
```

In the output, there will be a `.zip` file:

```
Target //salsa/gg:gg_cli up-to-date:
  bazel-bin/examples/par/my_binary
  bazel-bin/examples/par/my_binary.zip
```

The `zip` file can be executed directly with:

```
python bazel-bin/examples/par/my_binary.zip
```

Alternatively, for convenience:

```
echo '#!/usr/bin/env python' > my_executable_zip
cat bazel-bin/examples/par/my_binary.zip >> my_executable_zip
chmod +x my_executable_zip
```

Will produce an executable that you can run:

```
./my_executable_zip
```
