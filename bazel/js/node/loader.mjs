import { resolve as pathResolve, dirname } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { readFile } from 'fs/promises';
import { promises as fs } from 'fs';
import { log } from 'console';

var extensions = ['.js']

// Helper function to resolve paths using NODE_PATH
async function resolveWithNodePath(specifier, parentModuleURL) {
    if (specifier.startsWith('file://')) {
        return specifier;
    }

    if (specifier.startsWith('.')) {
        const filePath = new URL(parentModuleURL).pathname;
        const dirPath = dirname(filePath);
        const resolvedPath = pathResolve(dirPath, specifier);

        for (const ext of extensions) {
            try {
                const resolvedPathWithExt = resolvedPath + ext;
                await fs.access(resolvedPathWithExt);
                return pathToFileURL(resolvedPathWithExt).href;
            } catch (error) {
                // Uncomment for debugging
                // console.log("Error", error);
            }
        }
    }

    if (process.env.NODE_PATH) {
        const paths = process.env.NODE_PATH.split(':').map((p) => pathResolve(p));
        for (const basePath of paths) {
            // console.log("Trying path", basePath);
            try {
                const resolvedPath = pathResolve(basePath, specifier);
                // check for every extension
                for (const ext of extensions) {
                    try {
                        const resolvedPathWithExt = resolvedPath + ext;
                        await fs.access(resolvedPathWithExt);
                        return pathToFileURL(resolvedPathWithExt).href;
                    } catch (error) {
                        // Uncomment for debugging
                        // console.log("Error", error);
                    }
                }
            } catch {
                // Continue if path cannot be resolved
            }
        }
    }
    return ""
}

// The resolve function that Node.js expects
export async function resolve(specifier, context, defaultResolve) {
    const { parentURL } = context;

    // Use custom resolution logic if needed
    const resolved = await resolveWithNodePath(specifier, parentURL);

    if (resolved) {
        return { url: resolved, shortCircuit: true };
    }

    const defaultResolved = await defaultResolve(specifier, context, defaultResolve);
    return defaultResolved
}

export async function load(url, context, defaultLoad) {
    return defaultLoad(url, context, defaultLoad);
}
