import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs/promises';

export default defineConfig({
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
    ],
});
