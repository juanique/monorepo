const Module = require('module');

// HACK: late binding of `process.cwd()` to allow looking up first party modules from either
// the runfiles root (when running tests or using `bazel run`) or $EXECROOT/$BINDIR when using
// `js_run_binary`.
//
// We have to do late bindings here because `js_binary` bakes $PWD at the top of its launcher
// script before it correctly cd into $BINDIR for `js_run_binary`. Therefore, we force "re-evaluate"
// `NODE_PATH` at the beginning of the process.
const cwd = process.cwd();
const runfilesRoot = process.env.JS_BINARY__RUNFILES + '/_main';
if (cwd === runfilesRoot) {
    // js_binary invoked directly
    process.env.NODE_PATH = cwd;
} else {
    // js_binary invoked by js_run_binary
    // For better compatibility, look at runfiles first before looking up in $BINDIR
    process.env.NODE_PATH = `${runfilesRoot}:${cwd}`;
}
Module._initPaths();

// Small utility to switch the working directory of `js_binary` to the workspace directory
// when we use `bazel run` to invoke the binary.
if (process.env.BUILD_WORKSPACE_DIRECTORY) {
    process.chdir(process.env.BUILD_WORKSPACE_DIRECTORY);
}
