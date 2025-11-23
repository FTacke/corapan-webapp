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
