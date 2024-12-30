## Playwright example

There are few non hermetic dependencies that need to be installed on the machine.

### Ubuntu

```
sudo apt install -f libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxdamage1 libgbm1 libasound2
```

### Run the tests

```
bazel test //examples/playwright/ts_project_sources:test
```

it fails with:

```
==================== Test output for //examples/playwright/ts_project_sources:test:
First argument must use the object destructuring pattern: _
First argument must use the object destructuring pattern: _
```
