import { defineConfig } from 'vitest/config'

export default defineConfig({
    test: {
        reporters: ['verbose', 'junit'],
        outputFile: {
            junit: process.env.XML_OUTPUT_FILE,
        },
        environment: 'jsdom',
        globals: true,
        setupFiles: './bazel/js/vitest/vitest.setup.js'
    },
})
