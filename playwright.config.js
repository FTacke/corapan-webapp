/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = {
  timeout: 30_000,
  use: {
    headless: true,
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:8000',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
};
