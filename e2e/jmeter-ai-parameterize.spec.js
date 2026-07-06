const { test, expect } = require('@playwright/test');
const { login, openJmeterAssistant, loadSimpleJmeterTemplate } = require('./helpers/auth');

test.describe('JMeter AI 参数化', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await openJmeterAssistant(page);
    await loadSimpleJmeterTemplate(page);

    const httpNode = page.getByTestId('jmeter-tree-node').filter({ hasText: 'API 请求' });
    await httpNode.getByTestId('jmeter-tree-node-row').click();
    await expect(page.getByTestId('jmeter-ai-parameterize-button')).toBeVisible();
  });

  test('选中 HTTP 请求节点后显示 AI 参数化按钮', async ({ page }) => {
    await expect(page.getByTestId('jmeter-ai-parameterize-button')).toBeEnabled();
  });

  test('点击 AI 参数化按钮后弹出结果对话框或加载状态', async ({ page }) => {
    test.skip(process.env.E2E_RUN_AI !== 'true', '设置 E2E_RUN_AI=true 后才执行真实 AI 参数化调用');

    const responsePromise = page.waitForResponse((response) =>
      response.url().includes('/ai/jmeter/parameterize')
    ).catch(() => null);

    await page.getByTestId('jmeter-ai-parameterize-button').click();
    await responsePromise;

    await expect(
      page.locator('.el-dialog').filter({ hasText: /AI 参数化|参数化结果/ })
        .or(page.getByText(/参数化中|AI 分析中/))
    ).toBeVisible({ timeout: 30000 });
  });
});
