import { Page } from '@playwright/test';
import fs from 'fs';

export async function screenshot(page: Page, filename: string) {
    // Ensure screenshots directory exists
    const screenshotsDir = `${process.env.TEST_UNDECLARED_OUTPUTS_DIR}/screenshots`;
    await fs.promises.mkdir(screenshotsDir, { recursive: true });

    const path = `${screenshotsDir}/${filename}`;

    console.log("Writing screenshot to", path);
    // Take and save screenshot
    await page.screenshot({
        path: path,
        fullPage: true
    });
}
