import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs/promises';

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
            name: 'redirect-ts-to-js',
            configureServer(server) {
                server.middlewares.use((req, res, next) => {
                    let newUrl = ""
                    if (req.url.endsWith('.ts')) {
                        newUrl = req.url.replace(/\.ts$/, '.js');
                    } else if (req.url.endsWith('.tsx')) {
                        newUrl = req.url.replace(/\.tsx$/, '.js');
                    }

                    console.log("redirecting " + req.url + " to " + newUrl);
                    if (newUrl != "") {
                        res.writeHead(302, { Location: newUrl });
                        res.end();
                        return
                    }
                    next();
                });
            },
        },
        {
            name: 'custom-import-loader',
            async resolveId(source, importer, options) {
                console.log("resolving " + source);
                try {
                    console.log("checking " + source);
                    await fs.access(source);
                    console.log("resolved " + source);
                    return source;
                } catch (err) {
                    // File does not exist, fallback to default behavior.
                    console.log("not found " + source);
                }
                const currentDir = process.cwd();
                const candidate = currentDir + "/" + source + ".js"

                // If candidate file exists, return it.
                try {
                    await fs.access(candidate);
                    return candidate;
                } catch (err) {
                    // File does not exist, fallback to default behavior.
                    return null;
                }
            },
        }
    ],
});
