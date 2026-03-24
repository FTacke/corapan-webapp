const { test, expect } = require('@playwright/test');

const BASE = process.env.E2E_BASE_URL || 'http://127.0.0.1:8000';

async function login(page) {
  await page.goto(`${BASE}/login`);
  await expect(page.locator('#login-form')).toBeVisible();
  await page.fill('#login-username', 'e2e_user');
  await page.fill('#login-password', 'password123');

  await Promise.all([
    page.waitForURL(url => !url.pathname.endsWith('/login')),
    page.locator('#login-form button[type="submit"]').click(),
  ]);

  await expect(page.locator('[data-account-menu-trigger], [data-user-menu-toggle]')).toBeVisible();
}

async function expectProtectedAreaBlocked(page) {
  await page.goto(`${BASE}/auth/account/profile/page`);
  await page.waitForLoadState('networkidle');

  expect(page.url()).not.toContain('/auth/account/profile/page');

  const hasLoginForm = await page.locator('#login-form').count() > 0;
  const hasLoginLink = await page.getByRole('link', { name: /login/i }).count() > 0;
  const bouncedWithShowLogin = page.url().includes('showlogin=1');

  expect(hasLoginForm || hasLoginLink || bouncedWithShowLogin).toBeTruthy();
}

test('login smoke uses canonical public login and reaches an authenticated profile page', async ({ page }) => {
  await page.goto(`${BASE}/`);
  await page.getByRole('link', { name: /login/i }).click();
  await page.waitForURL(/\/login/);

  await login(page);

  await page.goto(`${BASE}/auth/account/profile/page`);
  await expect(page).toHaveURL(/\/auth\/account\/profile\/page$/);
  await expect(page.getByRole('heading', { name: /dein profil/i })).toBeVisible();
});

test('protected profile page blocks anonymous access', async ({ page }) => {
  await expectProtectedAreaBlocked(page);
});

test('logout smoke clears authenticated access to protected profile page', async ({ page }) => {
  await login(page);
  await page.goto(`${BASE}/auth/account/profile/page`);
  await expect(page).toHaveURL(/\/auth\/account\/profile\/page$/);

  await page.locator('[data-account-menu-trigger], [data-user-menu-toggle]').click();
  await expect(page.locator('[data-user-menu]')).toBeVisible();

  await Promise.all([
    page.waitForURL(url => !url.pathname.startsWith('/auth/account/profile')),
    page.locator('[data-logout="fetch"]').click(),
  ]);

  await page.waitForLoadState('networkidle');
  await expectProtectedAreaBlocked(page);
});

test('profile smoke renders current seeded account data', async ({ page }) => {
  await login(page);
  await page.goto(`${BASE}/auth/account/profile/page`);

  await expect(page.locator('#current-username')).toHaveText('e2e_user');
  await expect(page.locator('#current-email')).toHaveText(/e2e_user@example\.org/);
  await expect(page.locator('#save')).toBeVisible();
  await expect(page.locator('#delete-account-btn')).toBeVisible();
});

