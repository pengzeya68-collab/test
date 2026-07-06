const { test, expect } = require('@playwright/test');
const { login, openJmeterAssistant, loadSimpleJmeterTemplate } = require('./helpers/auth');

test.describe('JMeter 趋势对比与基线管理', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await openJmeterAssistant(page);
    await loadSimpleJmeterTemplate(page);
  });

  test('基线管理按钮可点击并打开对话框', async ({ page }) => {
    await page.getByRole('button', { name: /基线管理/ }).click();
    await expect(page.locator('.el-dialog').filter({ hasText: /基线/ })).toBeVisible();
  });

  test('基线列表表格或空状态可见', async ({ page }) => {
    await page.getByRole('button', { name: /基线管理/ }).click();
    const dialog = page.locator('.el-dialog').filter({ hasText: /基线/ });
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('.el-table').or(dialog.getByText(/暂无|空/))).toBeVisible();
  });

  test('趋势对比对话框在有压测结果后可打开', async ({ page }) => {
    test.skip(process.env.E2E_RUN_BENCH !== 'true', '设置 E2E_RUN_BENCH=true 后才执行真实压测趋势对比');

    await page.getByTestId('jmeter-bench-start-button').click();
    await expect(page.getByTestId('jmeter-bench-result-section')).toBeVisible({ timeout: 60000 });

    await page.getByRole('button', { name: /趋势对比/ }).click();
    await expect(page.locator('.el-dialog').filter({ hasText: /趋势/ })).toBeVisible();
  });
});
