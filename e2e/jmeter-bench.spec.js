const { test, expect } = require('@playwright/test');
const { login, openJmeterAssistant, loadSimpleJmeterTemplate } = require('./helpers/auth');

test.describe('JMeter 压测执行', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await openJmeterAssistant(page);
    await loadSimpleJmeterTemplate(page);
  });

  test('压测配置面板可见', async ({ page }) => {
    await expect(page.getByTestId('jmeter-bench-panel')).toBeVisible();
    await expect(page.getByTestId('jmeter-bench-engine-select')).toBeVisible();
    await expect(page.getByTestId('jmeter-bench-concurrency-input')).toBeVisible();
    await expect(page.getByTestId('jmeter-bench-duration-input')).toBeVisible();
    await expect(page.getByTestId('jmeter-bench-start-button')).toBeVisible();
  });

  test('引擎选择器包含快速预览和 JMeter 引擎选项', async ({ page }) => {
    await page.getByTestId('jmeter-bench-engine-select').click();
    await expect(page.getByRole('option', { name: /快速预览/ })).toBeVisible();
    await expect(page.getByRole('option', { name: /JMeter 引擎/ })).toBeVisible();
  });

  test('启动快速预览压测后显示进度或结果', async ({ page }) => {
    await page.getByTestId('jmeter-bench-engine-select').click();
    await page.getByRole('option', { name: /快速预览/ }).click();

    const concurrencyInput = page.getByTestId('jmeter-bench-concurrency-input').locator('input');
    await concurrencyInput.fill('1');
    const durationInput = page.getByTestId('jmeter-bench-duration-input').locator('input');
    await durationInput.fill('3');

    await page.getByTestId('jmeter-bench-start-button').click();

    await expect(
      page.getByTestId('jmeter-bench-progress').or(page.getByTestId('jmeter-bench-result-section'))
    ).toBeVisible({ timeout: 15000 });
  });
});
