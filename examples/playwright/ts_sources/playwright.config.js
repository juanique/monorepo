import { defineConfig, devices } from '@playwright/test';

async function createConfig() {
    process.env.PLAYWRIGHT_HTML_OUTPUT_DIR = process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/html";
    process.env.PLAYWRIGHT_JUNIT_OUTPUT_NAME = process.env.XML_OUTPUT_FILE;

    return defineConfig({
        // Look for test files in the "tests" directory, relative to this configuration file.
        testDir: '.',

        // Reporter to use
        reporter: [
            ['list', { printSteps: true }],
            ['junit'],
            ["html"],
        ],

        outputDir: process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/reports",

        projects: [
            {
                name: 'chromium',
                use: {
                    ...devices['Desktop Chrome'],
                    launchOptions: {
                        // When in CI, use bazel packaged linux chromium
                        executablePath: process.env.CHROMIUM_BIN,
                    },
                },
            },
        ],
    });
}

export default createConfig();
