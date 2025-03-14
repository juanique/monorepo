import { test, expect } from '@playwright/test';
import { screenshot } from 'salsa/testing/playwright/playwright';

test('has title', async ({ page }) => {
    await page.goto('https://playwright.dev/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Playwright/);

    // Take a screenshot using the utility
    await screenshot(page, 'has-title.png');
});

test('get started link', async ({ page }) => {
    await page.goto('https://playwright.dev/');

    // Click the get started link.
    await page.getByRole('link', { name: 'Get started' }).click();

    // Expects page to have a heading with the name of Installation.
    await expect(page.getByRole('heading', { name: 'Installation' })).toBeVisible();

    // Take a screenshot using the utility
    await screenshot(page, 'get-started.png');
});
