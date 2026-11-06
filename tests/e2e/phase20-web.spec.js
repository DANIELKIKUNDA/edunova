const { test, expect, devices } = require('@playwright/test');

const baseURL = process.env.EDUNOVA_WEB_URL || 'http://127.0.0.1:8080';

async function assertFlutterStarted(page) {
  // Flutter keeps connections/workers active; networkidle is not a readiness signal.
  await page.goto(baseURL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForFunction(() =>
    document.querySelector('flt-glass-pane, flutter-view, canvas') !== null,
    null,
    { timeout: 120000 }
  );
  await expect(page.locator('body')).toBeVisible();
}

test('desktop application boots without page errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await assertFlutterStarted(page);
  await page.screenshot({ path: 'certification-results/e2e/desktop-home.png', fullPage: true });
  expect(errors).toEqual([]);
});

test.describe('modest Android viewport', () => {
  // Device presets include defaultBrowserType, which Playwright forbids inside describe.
  // Apply only the Chromium context options for this mobile viewport.
  const phone = devices['Galaxy S9+'];
  test.use({
    viewport: phone.viewport,
    userAgent: phone.userAgent,
    deviceScaleFactor: phone.deviceScaleFactor,
    isMobile: phone.isMobile,
    hasTouch: phone.hasTouch,
  });

  test('mobile surface renders and remains usable', async ({ page }) => {
    await assertFlutterStarted(page);
    const viewport = page.viewportSize();
    expect(viewport.width).toBeLessThanOrEqual(480);
    await page.screenshot({ path: 'certification-results/e2e/android-modest-home.png', fullPage: true });
  });

  test('active application stays rendered during a network interruption and recovers', async ({ page, context }) => {
    await assertFlutterStarted(page);
    const flutterSurface = page.locator('flutter-view, flt-glass-pane').first();
    await expect(flutterSurface).toBeVisible();
    try {
      await context.setOffline(true);
      // Check the actual Flutter surface, not just the browser error page's body.
      await expect(flutterSurface).toBeVisible();
      await page.screenshot({ path: 'certification-results/e2e/android-offline-active.png', fullPage: true });
    } finally {
      await context.setOffline(false);
    }
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 30000 });
    await expect(flutterSurface).toBeVisible();
  });
});

test('static resources satisfy a modest-device transfer budget', async ({ page }) => {
  let transferred = 0;
  page.on('response', async response => {
    const value = Number((await response.allHeaders())['content-length'] || 0);
    transferred += value;
  });
  await assertFlutterStarted(page);
  // A generous regression guard, not a claim of laboratory device profiling.
  expect(transferred).toBeLessThan(35 * 1024 * 1024);
});
