import { cwd as getCwd } from 'process';
import { env, chdir } from 'process';
import Module from 'module';
import { register } from 'node:module';
import { resolve } from 'path';
import { pathToFileURL } from 'url';



// HACK: late binding of `process.cwd()` to allow looking up first-party modules from either
// the runfiles root (when running tests or using `bazel run`) or $EXECROOT/$BINDIR when using
// `js_run_binary`.
//
// We have to do late bindings here because `js_binary` bakes $PWD at the top of its launcher
// script before it correctly cd into $BINDIR for `js_run_binary`. Therefore, we force "re-evaluate"
// `NODE_PATH` at the beginning of the process.
const cwd = getCwd();
const runfilesRoot = `${env.JS_BINARY__RUNFILES}/_main`;

if (cwd === runfilesRoot) {
    // js_binary invoked directly
    env.NODE_PATH = cwd;
} else {
    // js_binary invoked by js_run_binary
    // For better compatibility, look at runfiles first before looking up in $BINDIR
    env.NODE_PATH = `${runfilesRoot}:${cwd}`;
}

// Initialize module paths
Module._initPaths();

// Register the custom loader
var resolved = resolve('./bazel/js/node/loader.mjs')
var loader = pathToFileURL(resolved).href;
register(loader);

// Small utility to switch the working directory of `js_binary` to the workspace directory
// when we use `bazel run` to invoke the binary.
if (env.BUILD_WORKSPACE_DIRECTORY) {
    chdir(env.BUILD_WORKSPACE_DIRECTORY);
}
