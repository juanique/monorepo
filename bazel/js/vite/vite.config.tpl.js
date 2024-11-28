import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import * as fs from 'fs';


function changeExtensionToJS(filename) {
    const parts = filename.split('.');
    if (parts.length === 1) {
        // No extension, add ".js" directly
        return `${filename}.js`;
    }
    // Replace the last part with "js"
    parts[parts.length - 1] = "js";
    return parts.join('.');
}

export default defineConfig({
    clearScreen: false,
    root: '.',
    server: {
        port: 3000,
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
                        const result = source.startsWith('/') ? source.slice(1) : source;

                        if (result.endsWith('.ts')) {
                            return result.replace(/\.ts$/, '.js');
                        }
                        return null; // Let Vite handle other resolutions
                    },
                },
            ],
        },
    },

    plugins: [
        react(),
        {
            name: 'redirect-root',
            configureServer(server) {
                server.middlewares.use((req, res, next) => {
                    // Redirect root to the index file in the package.
                    if (req.url === '/') {
                        res.writeHead(302, { Location: '/{PACKAGE}/index.html' });
                        res.end();
                    } else {
                        next();
                    }
                });
            },
        },
        {
            name: 'custom-import-loader',
            resolveId(source, importer, options) {
                console.log("resolving " + source);
                // remove leading slash if present
                candidate = source.startsWith('/') ? source.slice(1) : source;
                // Check relative to root
                candidate = process.cwd() + "/" + candidate;

                if (candidate.endsWith(".ts")) {
                    resolved = changeExtensionToJS(candidate);
                    console.log("resolved " + source + " to " + resolved);
                    return resolved;
                }

                if (candidate.endsWith(".tsx")) {
                    resolved = changeExtensionToJS(candidate);
                    console.log("resolved " + source + " to " + resolved);
                    return resolved;
                }

                if (!candidate.includes(".")) {
                    resolved = changeExtensionToJS(candidate);
                    console.log("resolved " + source + " to " + resolved);
                    return resolved;
                }

                console.log("resolved " + source + " to " + candidate);
                return candidate;
            },
        }
    ],
});
