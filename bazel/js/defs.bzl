load("//bazel/js:js.bzl", _js_binary = "js_binary", _js_library = "js_library")
load("//bazel/js:ts.bzl", _ts_binary = "ts_binary", _ts_library = "ts_library")
load("//bazel/js/vite:vite.bzl", _vite_webapp = "vite_webapp")
load("//bazel/js/vitest:vitest.bzl", _vitest_test = "vitest_test")
load("//bazel/playwright:defs.bzl", _playwright_test = "playwright_test")
load("//bazel/js/react:react.bzl", _react_app = "react_app", _react_boilerplate = "react_boilerplate")

js_binary = _js_binary
js_library = _js_library
ts_binary = _ts_binary
ts_library = _ts_library
vite_webapp = _vite_webapp
vitest_test = _vitest_test
playwright_test = _playwright_test
react_boilerplate = _react_boilerplate
react_app = _react_app
