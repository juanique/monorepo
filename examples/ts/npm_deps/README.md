## To install npm deps:

```
bazel run -- @pnpm//:pnpm --dir $PWD -w install chalk figlet
```

Some packages may need extra deps for type resolution.

```
bazel run -- @pnpm//:pnpm --dir $PWD -w install --save-dev @types/figlet
```

To run the example:

```
bazel run //examples/ts/npm_deps:main
```
