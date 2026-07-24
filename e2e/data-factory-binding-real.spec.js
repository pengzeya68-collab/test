const { test, expect } = require('@playwright/test');
const { login } = require('./helpers/auth');

test.describe('测试数据工厂真实绑定工作流', () => {
  test('未预绑定模板生成的数据可从桌面界面绑定到场景并持久化', async ({ page }) => {
    await login(page);
    const backendURL = process.env.E2E_BACKEND_URL || 'http://127.0.0.1:5101';
    const token = await page.evaluate(() => localStorage.getItem('token'));
    const headers = { Authorization: `Bearer ${token}` };
    const suffix = Date.now();
    const scenarioName = `E2E 数据绑定场景 ${suffix}`;
    const templateName = `E2E 未绑定模板 ${suffix}`;

    const scenarioResponse = await page.request.post(`${backendURL}/api/auto-test/scenarios`, {
      headers,
      data: { name: scenarioName, description: '端到端验收数据', is_active: true },
    });
    expect(scenarioResponse.ok()).toBeTruthy();
    const scenario = await scenarioResponse.json();

    const templateResponse = await page.request.post(`${backendURL}/api/auto-test/data-factory/templates`, {
      headers,
      data: {
        name: templateName,
        description: '生成后再绑定的模板',
        scenario_id: null,
        row_count: 2,
        fields: [{
          field_name: 'account',
          field_label: '测试账号',
          rule_type: 'fixed',
          rule_config: { value: `account-${suffix}` },
          sort_order: 0,
        }],
      },
    });
    expect(templateResponse.ok()).toBeTruthy();

    try {
      await page.goto('/#/data-factory');
      await page.locator('.tpl-item').filter({ hasText: templateName }).click();
      await expect(page.getByRole('button', { name: '生成数据集', exact: true })).toBeVisible();
      await page.getByRole('button', { name: '生成数据集', exact: true }).click();
      await expect(page.locator('.result-card').getByText('数据集已生成', { exact: true })).toBeVisible();

      await page.getByRole('button', { name: '绑定场景', exact: true }).click();
      const dialog = page.getByRole('dialog', { name: '绑定到测试场景' });
      await dialog.locator('.el-select').click();
      await page.getByRole('option', { name: scenarioName, exact: true }).click();
      await dialog.getByRole('button', { name: '绑定', exact: true }).click();
      await expect(page.getByText('绑定成功', { exact: true })).toBeVisible();

      const datasetResponse = await page.request.get(`${backendURL}/api/auto-test/scenarios/${scenario.id}/dataset`, { headers });
      expect(datasetResponse.ok()).toBeTruthy();
      const dataset = await datasetResponse.json();
      expect(dataset.data_matrix).toEqual({
        columns: ['account'],
        rows: [[`account-${suffix}`], [`account-${suffix}`]],
      });
    } finally {
      await page.request.delete(`${backendURL}/api/auto-test/scenarios/${scenario.id}`, { headers });
    }
  });
});
