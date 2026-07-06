const { expect } = require('@playwright/test');

async function login(page) {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/#/login');

  await expect(page.getByTestId('login-page')).toBeVisible();
  await page.getByTestId('login-username-input').locator('input').fill(process.env.E2E_USERNAME || 'admin');
  await page.getByTestId('login-password-input').locator('input').fill(process.env.E2E_PASSWORD || '123456');
  await page.getByTestId('login-submit-button').click();

  await expect(page).not.toHaveURL(/#\/login(?:$|[/?])/);
}

async function openJmeterAssistant(page) {
  await page.goto('/#/auto-test');
  await expect(page.getByTestId('auto-test-page')).toBeVisible();
  await page.getByTestId('auto-test-group-tools').click();
  await page.getByTestId('auto-test-tab-jmeter').click();
  await expect(page.getByTestId('auto-test-panel-jmeter')).toBeVisible();
  await expect(page.getByTestId('jmeter-page')).toBeVisible();
}

async function loadSimpleJmeterTemplate(page) {
  await page.locator('.tpl-card').filter({ hasText: '简单 API 验证' }).click();
  await expect(page.getByTestId('jmeter-step-configure')).toHaveClass(/active/);
  await expect(page.getByTestId('jmeter-tree-panel')).toBeVisible();
  await expect(page.getByTestId('jmeter-tree-node').filter({ hasText: 'API 请求' })).toBeVisible();
}

module.exports = {
  login,
  openJmeterAssistant,
  loadSimpleJmeterTemplate,
};
