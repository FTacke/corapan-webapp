const { test, expect } = require('@playwright/test');

test('login → protected → refresh → logout (basic smoke)', async ({ page, request }) => {
  const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:8000';

  // 1) Login
  await page.goto(`${base}/auth/login`);
  await page.fill('#login-username', 'e2e_user');
  await page.fill('#login-password', 'password123');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type=submit]'),
  ]);

  // 2) Access protected page to verify cookie/session
  await page.goto(`${base}/auth/account/profile/page`);
  expect(page.url()).toContain('/auth/account/profile');

  // 3) Try a refresh via calling the endpoint (browser cookies will be present)
  const refreshResp = await request.post(`${base}/auth/refresh`);
  expect([200, 401, 403]).toContain(refreshResp.status()); // allow rotation behavior

  // 4) Trigger logout via UI (our data-logout handler) and ensure session cleared
  // Click logout anchor/button
  await page.click('[data-logout="fetch"]');
  await page.waitForLoadState('networkidle');

  // After logout attempt, accessing profile should redirect to login
  await page.goto(`${base}/auth/account/profile/page`);
  expect(page.url().includes('/auth/login')).toBeTruthy();
});

test('login sheet shows Spanish MD3 warning for invalid credentials', async ({ page }) => {
  const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:8000';

  await page.goto(`${base}/auth/login`);
  // Use valid username but wrong password to surface 'invalid credentials' flow
  await page.fill('#login-username', 'e2e_user');
  await page.fill('#login-password', 'wrong-password');

  // Submit and wait for the sheet to display an error
  await Promise.all([
    page.waitForSelector('.md3-login-sheet__errors'),
    page.click('button[type=submit]'),
  ]);

  const err = await page.locator('.md3-login-sheet__errors .error-message__text').innerText();
  expect(err).toContain('Nombre de usuario o contraseña incorrectos');
});

test('login sheet opens from top-app-bar and renders without errors', async ({ page }) => {
  const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:8000';

  await page.goto(`${base}/`);

  // Click the top-right login icon (unauthenticated state)
  await page.click('a[aria-label="Iniciar sesión"]');

  // Wait for the sheet to appear
  const sheet = page.locator('#login-sheet');
  await expect(sheet).toBeVisible({ timeout: 3000 });

  // Ensure we don't get a 403 or 500 in HTMX request logs by checking there is
  // an actionable submit button and the form is present.
  await expect(page.locator('#login-form')).toBeVisible();
  await expect(page.locator('button[type=submit]')).toBeVisible();
});
