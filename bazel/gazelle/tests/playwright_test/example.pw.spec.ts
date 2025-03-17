import { test, expect } from '@playwright/test';

test('typescript test', async ({ page }) => {
    const url: string = 'https://example.com';
    await page.goto(url);
    await expect(page).toHaveTitle(/Example/);
});
