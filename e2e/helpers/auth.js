const { expect } = require('@playwright/test');

async function login(page) {
  await page.setViewportSize({ width: 1440, height: 900 });
  const backendURL = process.env.E2E_BACKEND_URL || 'http://127.0.0.1:5101';
  const response = await page.request.post(`${backendURL}/api/v1/auth/login`, {
    data: {
      username: process.env.E2E_USERNAME || 'admin',
      password: process.env.E2E_PASSWORD || 'admin123',
    },
  });
  if (!response.ok()) {
    throw new Error(`E2E 登录接口返回 ${response.status()}: ${await response.text()}`);
  }
  const session = await response.json();
  await page.addInitScript(({ token, user, serverURL }) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('testmaster_server_url', serverURL);
  }, { token: session.access_token, user: session.user, serverURL: backendURL });
  await page.goto('/#/');
  // Wait for the authenticated home page. This button is a stable navigation
  // contract, unlike a historical page heading that no longer exists.
  await expect(page.getByRole('button', { name: '进入自动化工作台', exact: true })).toBeVisible({ timeout: 20_000 });
}

async function openJmeterAssistant(page) {
  await page.goto('/#/jmeter-assistant');
  // The assistant is a large lazy-loaded editor. On a clean Vite cache six
  // parallel browser workers can compile it after navigation, so use a
  // deterministic cold-start allowance instead of the global 5-second expect.
  await expect(page.getByTestId('jmeter-page')).toBeVisible({ timeout: 20_000 });
}

function httpRequestNode(page) {
  return page.locator('[data-testid="jmeter-tree-node"][data-node-type="HttpSampler"]');
}

async function loadSimpleJmeterTemplate(page) {
  await page.locator('.tpl-card').filter({ hasText: '简单 API 验证' }).click();
  await expect(page.getByTestId('jmeter-step-configure')).toHaveClass(/active/);
  await expect(page.getByTestId('jmeter-tree-panel')).toBeVisible();
  await expect(httpRequestNode(page)).toBeVisible();
}

module.exports = {
  login,
  openJmeterAssistant,
  loadSimpleJmeterTemplate,
  httpRequestNode,
};
