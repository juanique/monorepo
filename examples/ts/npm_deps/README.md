## To install npm deps:

```
bazel run -- @pnpm//:pnpm --dir $PWD install -w chalk figlet
```

Some packages may need extra deps for type resolution.

```
bazel run -- @pnpm//:pnpm --dir $PWD install -w @types/figlet
```
