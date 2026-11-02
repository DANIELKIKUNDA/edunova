const { test, expect, devices } = require('@playwright/test');

const baseURL = process.env.EDUNOVA_WEB_URL || 'http://127.0.0.1:8080';

async function assertFlutterStarted(page) {
  await page.goto(baseURL, { waitUntil: 'networkidle', timeout: 120000 });
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
  test.use({ ...devices['Galaxy S9+'] });

  test('mobile surface renders and remains usable', async ({ page }) => {
    await assertFlutterStarted(page);
    const viewport = page.viewportSize();
    expect(viewport.width).toBeLessThanOrEqual(480);
    await page.screenshot({ path: 'certification-results/e2e/android-modest-home.png', fullPage: true });
  });

  test('installed application survives a network interruption', async ({ page, context }) => {
    await assertFlutterStarted(page);
    await page.waitForTimeout(3000);
    await context.setOffline(true);
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
    await expect(page.locator('body')).toBeVisible();
    await page.screenshot({ path: 'certification-results/e2e/android-offline-reload.png', fullPage: true });
    await context.setOffline(false);
    await page.reload({ waitUntil: 'networkidle', timeout: 120000 });
    await expect(page.locator('body')).toBeVisible();
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
