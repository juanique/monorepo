import { Page } from '@playwright/test';

export async function test(page: Page) {
    await page.goto('https://example.com');
}
