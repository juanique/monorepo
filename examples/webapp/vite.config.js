import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

import fs from 'fs/promises'; // Import the file system module
import { hasUncaughtExceptionCaptureCallback } from 'process';

console.log('***********************************');
const projectRoot = process.cwd(); // Current working directory
console.log('Vite Project Root:', projectRoot);


export default defineConfig({
    root: '.',
    server: {
        port: 3000, // Specify the port number
    },
    build: {
        outDir: './dist', // Specify the output directory for the build
        rollupOptions: {
            plugins: [
                {
                    name: 'copy-html-plugin',
                    buildStart: async () => {
                        try {
                            // 1. Read the index.html file
                            const htmlContent = await fs.readFile('./examples/webapp/index.html', 'utf-8');

                            // 2. Write the file to the destination (project root)
                            await fs.writeFile('./index.html', htmlContent);
                            console.log('index.html copied to vite project root');
                            // await fs.writeFile('./dist/index.html', htmlContent);
                        } catch (err) {
                            console.error('Error copying index.html:', err);
                        }
                    },
                    writeBundle: async () => {
                        // List all files in the dist directory, recursively

                        // Move ./dist to examples/webapp/dist
                        await fs.rename('./dist', 'examples/webapp/dist');
                        // create dist directory
                        // await fs.mkdir('examples/webapp/dist', { recursive: true });
                        // write something to it
                        // await fs.writeFile('examples/webapp/dist/test.txt', 'test');
                        console.log('Current working directory is :', process.cwd());
                        // console.log("pp")

                        const files = await fs.readdir('./', { recursive: true });
                        for (const file of files) {
                            // If contains dist, log the file and not node_modules
                            if (file.includes('dist') && !file.includes('node_modules')) {
                                console.log(file);
                            }
                        }
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
                    if (req.url === '/') {
                        req.url = '/examples/webapp/index.html'; // Redirect to the desired file
                    }
                    next();
                });
            },
        },
    ],
});
