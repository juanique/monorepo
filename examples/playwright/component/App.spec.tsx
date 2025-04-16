import { test, expect } from '@playwright/experimental-ct-react';
import React from 'react';
import { App } from './App';

test.describe('App', () => {
    test('should render hello message', async ({ mount }) => {
        const component = await mount(<App />);

        // Check if the heading is visible
        const heading = component.getByText('Hello Playwright');
        await expect(heading).toBeVisible();

        // Check if the button exists
        const button = component.getByText('Click me');
        await expect(button).toBeVisible();
    });

    test('should have correct structure', async ({ mount }) => {
        const component = await mount(<App />);

        // Check if the main container has the correct test id
        const container = component.getByTestId('app');
        await expect(container).toBeVisible();

        // Verify the container has both the heading and button
        await expect(container.getByRole('heading')).toBeVisible();
        await expect(container.getByRole('button')).toBeVisible();
    });
});
