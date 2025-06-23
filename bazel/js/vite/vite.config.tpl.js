import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs/promises';
import fsSync from "fs"
import path from 'path';
import tailwindcss from '@tailwindcss/vite'

function changeExtensionToJS(filename) {
    var parts = filename.split("/")
    var dirName = parts.slice(0, -1).join("/")
    var fileName = parts.pop()

    const fileparts = fileName.split('.');
    if (fileparts.length === 1) {
        // No extension, add ".js" directly
        return `${dirName}/${fileName}.js`;
    }
    // Replace the last part with "js"
    fileparts[fileparts.length - 1] = "js";
    filename = fileparts.join('.');
    return `${dirName}/${filename}`;
}

function resolveSource(source) {
    if (source.replace(/^\x00/, '').startsWith("vite")) {
        console.log("resolving " + source + " to " + source);
        return source;
    } else {
        console.log(source + " does not start with vite");
    }

    // remove leading slash if present
    var candidate = source.startsWith('/') ? source.slice(1) : source;
    // Check relative to root
    candidate = process.cwd() + "/" + candidate;

    if (candidate.endsWith(".ts")) {
        var resolved = changeExtensionToJS(candidate);
        console.log("resolved " + source + " to " + resolved);
        return resolved;
    }

    if (candidate.endsWith(".tsx")) {
        var resolved = changeExtensionToJS(candidate);
        console.log("resolved " + source + " to " + resolved);
        return resolved;
    }

    var filename = candidate.split('/').pop();
    if (!filename.includes(".")) {
        var resolved = changeExtensionToJS(candidate);
        console.log("resolved " + source + " to " + resolved);
        return resolved;
    }

    console.log("resolved " + source + " to " + candidate);
    return candidate;

}

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');

    return {
        clearScreen: false,
        root: '.',
        server: {
            port: 3000,
        },
        define: {
            "process.env": env,
        },
        build: {
            outDir: './{PACKAGE}/dist', // Specify the output directory for the build
            rollupOptions: {
                plugins: [
                    {
                        name: 'copy-html-plugin',
                        buildStart: async () => {
                            try {
                                // Move index.html to the root of the project so vite can find it.
                                const htmlContent = await fs.readFile('./{PACKAGE}/index.html', 'utf-8');
                                await fs.writeFile('./index.html', htmlContent);
                                console.log('index.html copied to vite project root');
                            } catch (err) {
                                console.error('Error copying index.html:', err);
                            }
                        },
                    },
                    {
                        name: 'resolve-ts-to-js',
                        apply: 'build', // Only apply this plugin during the build
                        resolveId(source) {
                            return resolveSource(source);
                        },
                    },
                ],
            },
        },

        plugins: [
            tailwindcss(),
            react(),
            {
                name: 'redirect-root',
                configureServer(server) {
                    server.middlewares.use((req, res, next) => {
                        if (req.url === '/') {
                            // When people go to the root, we redirect them to the index.html in the package.
                            console.log("Redirecting to /{PACKAGE}/index.html");
                            res.writeHead(302, { Location: '/{PACKAGE}/index.html' });
                            res.end();
                        } else if (req.url.startsWith('/{PACKAGE}') && !req.url.includes('.')) { // No file extension in the URL
                            // When people request other urls relative to the
                            // package that are not resources (.js, .css, etc)
                            // we serve index.html so that the react router can
                            // take over.
                            const indexHtmlPath = path.resolve(__dirname, "index.html")
                            console.log("Serving index.html for " + req.url);
                            const htmlContent = fsSync.readFileSync(indexHtmlPath, 'utf-8'); // Synchronously read the index.html file
                            res.setHeader('Content-Type', 'text/html');
                            res.end(htmlContent); // Send the content of index.html as the response
                        } else {
                            next(); // Proceed to the next middleware if it's a file request
                        }
                    });
                },
            },

            {
                name: 'custom-import-loader',
                resolveId(source, importer, options) {
                    return resolveSource(source);
                },
            },
        ],
    };
});

