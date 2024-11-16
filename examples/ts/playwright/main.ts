import { chromium } from 'playwright';

// Named async function
async function runPlaywrightTest() {

    console.log('Launching Chromium browser...');
    // Launch a Chromium browser
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/home/juanique/bin/chromedriver',
    });
    console.log('Chromium browser launched');
    const context = await browser.newContext();
    console.log('New context created');
    const page = await context.newPage();
    console.log('New page created');
    // Navigate to Google
    console.log('Navigating to Google...');
    await page.goto('https://www.google.com');
    console.log('Navigated to Google');

    await page.screenshot({ path: '/home/juanique/tmp/screenshot-headless.png' });
    console.log('Screenshot taken: /home/juanique/tmp/screenshot-headless.png');


    // Get the page title and assert that it contains "Google"
    const title = await page.title();
    if (!title.includes('Google')) {
        throw new Error(`Assertion failed: Title does not contain "Google". Found: ${title}`);
    }

    console.log('Test passed: Title contains "Google"');

    // Close the browser
    await browser.close();
}

// Call the named function
runPlaywrightTest();
