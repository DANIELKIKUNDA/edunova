const { test, expect } = require('@playwright/test');

const apiBase = process.env.EDUNOVA_API_URL || 'http://127.0.0.1:8000';

async function openLogin(page) {
  await page.goto('/#/login', { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.locator('flutter-view').waitFor({ state: 'attached', timeout: 120000 });

  // Flutter renders to a canvas until browser accessibility semantics are enabled.
  // Activating the placeholder exposes the same labelled controls used by a
  // keyboard or assistive technology, which makes this a real user-level test.
  const semanticsPlaceholder = page.locator('flt-semantics-placeholder');
  if (await semanticsPlaceholder.count()) {
    await semanticsPlaceholder.evaluate((element) => element.click());
  }

  await expect(page.getByText('Retrouve ton EduNova')).toBeVisible({ timeout: 120000 });
}

test('student login crosses Flutter Web, API and PostgreSQL', async ({ page, request }) => {
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const email = `phase21-ui-${suffix}@example.test`;
  const password = 'Phase21-UI-Password!';

  const registration = await request.post(`${apiBase}/v1/identity/register`, {
    data: {
      display_name: 'Phase 21 Web Student',
      email,
      password,
      device_name: 'phase21-api-seed',
    },
  });
  expect(registration.status()).toBe(201);
  const seedSession = await registration.json();

  await openLogin(page);
  await page.getByLabel('Téléphone ou e-mail').fill(email);
  await page.getByLabel('Mot de passe', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Se connecter' }).click();

  await expect(page).toHaveURL(/#\/bootstrap/, { timeout: 120000 });
  await page.screenshot({
    path: 'certification-results/phase21/flutter-web-authenticated.png',
    fullPage: true,
  });

  const sessions = await request.get(`${apiBase}/v1/identity/sessions`, {
    headers: { Authorization: `Bearer ${seedSession.access_token}` },
  });
  expect(sessions.status()).toBe(200);
  const devices = (await sessions.json()).filter((item) => item.active).map((item) => item.device_name);
  expect(devices).toContain('phase21-api-seed');
  expect(devices).toContain('EduNova');
});

test('invalid credentials remain visibly rejected by Flutter Web', async ({ page }) => {
  await openLogin(page);
  await page.getByLabel('Téléphone ou e-mail').fill('unknown-phase21@example.test');
  await page.getByLabel('Mot de passe', { exact: true }).fill('Wrong-Password!');
  await page.getByRole('button', { name: 'Se connecter' }).click();
  await expect(page.getByText('Connexion impossible. Vérifie tes identifiants et la connexion.')).toBeVisible();
  await page.screenshot({
    path: 'certification-results/phase21/flutter-web-invalid-login.png',
    fullPage: true,
  });
});
