import { cwd as getCwd } from 'process';
import { env, chdir } from 'process';
import Module from 'module';
import { register } from 'node:module';
import { resolve } from 'path';
import { pathToFileURL } from 'url';


// Laucher that sets NODE_PATH in a way that is bazel-friendly.
// It also registers a custom loader that can resolve modules from NODE_PATH in ESModules
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
