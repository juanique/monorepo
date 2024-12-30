import { defineConfig, devices } from '@playwright/test';

async function createConfig() {

    process.env.PLAYWRIGHT_HTML_OUTPUT_DIR = process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/html";
    process.env.PLAYWRIGHT_JUNIT_OUTPUT_NAME = process.env.XML_OUTPUT_FILE;

    return defineConfig({
        // Look for test files in the "tests" directory, relative to this configuration file.
        testDir: '.',

        // Run all tests in parallel.
        fullyParallel: true,

        // Fail the build on CI if you accidentally left test.only in the source code.
        forbidOnly: !!process.env.CI,

        use: {
            trace: 'retain-on-failure',
        },

        build: {
            external: ['**/*'],
        },

        testMatch: '**/*.spec.js',

        contextOptions: {
            recordVideo: {
                dir: process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/videos",
                size: { width: 640, height: 480 },
            }
        },

        // Reporter to use
        reporter: [
            ['list', { printSteps: true }],
            ['junit'],
            ["html"],
        ],

        outputDir: process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/reports",

        // Configure projects for major browsers.
        projects: [
            {
                name: 'chromium',
                use: {
                    ...devices['Desktop Chrome'],
                    launchOptions: {
                        // When in CI, use bazel packaged linux chromium
                        executablePath: process.env.CHROMIUM_BIN,
                    },
                    viewport: { width: 640, height: 480 },
                },
            },
        ],
    });
}

export default createConfig();
