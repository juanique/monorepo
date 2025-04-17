import { defineConfig, devices } from '@playwright/experimental-ct-react';
import fs from 'fs/promises'; // Note the /promises for async/await

console.log(process.version);


// TODO: playwright component testing seems to expect an index.html file.
// One option would be to write the file here, another option is to have bazel provide the file.
async function createIndexHtml() {
    const content = `
<html lang="en">
  <body>
    <div id="root"></div>
  </body>
</html>
`;
    try {
        await fs.mkdir('./playwright', { recursive: true });
        await fs.writeFile('./playwright/index.html', content);
        console.log('File created successfully!');
        console.log("PWD:", process.cwd());
    } catch (err) {
        console.error(err);
    }
}

async function createConfig() {
    process.env.PLAYWRIGHT_HTML_OUTPUT_DIR = process.env.TEST_UNDECLARED_OUTPUTS_DIR + "/html";
    process.env.PLAYWRIGHT_JUNIT_OUTPUT_NAME = process.env.XML_OUTPUT_FILE;
    process.env.PW_TEST_HTML_REPORT_OPEN = "never";

    await createIndexHtml();

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

        use: {
            ctPort: 3000,

        },

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
