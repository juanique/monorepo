import { defineConfig, devices } from '@playwright/experimental-ct-react';

async function createConfig() {
    process.env.PLAYWRIGHT_HTML_OUTPUT_DIR = process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/html";
    process.env.PLAYWRIGHT_JUNIT_OUTPUT_NAME = process.env.XML_OUTPUT_FILE;
    process.env.PW_TEST_HTML_REPORT_OPEN = "never";

    return defineConfig({
        // Look for test files in the "tests" directory, relative to this configuration file.
        testDir: '.',

        expect: {
            // Maximum time expect() should wait for the condition to be met.
            timeout: 1000,
        },

        // Reporter to use
        reporter: [
            ['list', { printSteps: true }],
            ['junit'],
            ["html", { open: 'never' }],
        ],

        // Note: may want to assign a random port per test so they can run in parallel.
        // It will work fine with network sandbox enabled on Linux, but OSX will be sad.
        //use: { ctPort: 3100 }

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
