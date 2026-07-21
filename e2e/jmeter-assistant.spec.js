const { test, expect } = require('@playwright/test');
const { login, openJmeterAssistant, loadSimpleJmeterTemplate, httpRequestNode } = require('./helpers/auth');

test.describe('JMeter 助手主流程', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await openJmeterAssistant(page);
  });

  test('页面加载并显示步骤向导', async ({ page }) => {
    await expect(page.getByTestId('jmeter-step-select-interface')).toBeVisible();
    await expect(page.getByTestId('jmeter-step-configure')).toBeVisible();
    await expect(page.getByTestId('jmeter-step-export')).toBeVisible();
  });

  test('可从模板进入脚本编辑步骤', async ({ page }) => {
    await loadSimpleJmeterTemplate(page);
    await expect(page.getByTestId('jmeter-bench-panel')).toBeVisible();
    await expect(page.getByTestId('jmeter-tree-add-threadgroup-button')).toBeVisible();
  });

  test('脚本编辑器可选择 HTTP 请求节点', async ({ page }) => {
    await loadSimpleJmeterTemplate(page);

    const httpNode = httpRequestNode(page);
    await httpNode.getByTestId('jmeter-tree-node-row').click();

    await expect(page.getByTestId('jmeter-ai-parameterize-button')).toBeVisible();
    await expect(page.getByText('请求名称', { exact: true })).toBeVisible();
    await expect(page.getByText('URL', { exact: true })).toBeVisible();
  });

  test('生成预览后进入 JMX 导出步骤', async ({ page }) => {
    await loadSimpleJmeterTemplate(page);

    await page.getByRole('button', { name: /生成预览/ }).click();
    await expect(page.getByTestId('jmeter-step-export')).toHaveClass(/active/);
  });
});
