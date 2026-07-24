const { test, expect } = require('@playwright/test');
const { login } = require('./helpers/auth');

const scenario = {
  id: 81,
  name: '零步骤场景',
  description: '用于验证场景编辑入口和空场景保护',
  is_active: true,
  step_count: 0,
};

async function installScenarioApiMocks(page) {
  const json = (route, body, status = 200) => route.fulfill({
    status,
    contentType: 'application/json; charset=utf-8',
    body: JSON.stringify(body),
  });

  await page.route('**/api/auto-test/environments**', route => json(route, [
    { id: 7, name: '测试环境', is_default: true },
  ]));
  await page.route('**/api/auto-test/scenarios/81/history**', route => json(route, { items: [] }));
  await page.route('**/api/auto-test/scenarios/81', route => json(route, { ...scenario, steps: [] }));
  await page.route('**/api/auto-test/scenarios**', route => json(route, { items: [scenario], total: 1 }));
}

test.describe('业务场景独立页面工作流', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await installScenarioApiMocks(page);
  });

  test('编辑入口进入场景编辑器，空场景运行会给出明确提示', async ({ page }) => {
    await page.goto('/#/scenarios');
    await expect(page.getByText('零步骤场景', { exact: true })).toBeVisible();

    await page.getByRole('button', { name: '编辑', exact: true }).click();
    await expect(page).toHaveURL(/#\/scenarios\/81$/);
    await expect(page.getByRole('button', { name: '添加步骤', exact: true }).first()).toBeVisible();

    await page.getByRole('button', { name: '运行场景', exact: true }).click();
    await expect(page.getByText('当前场景没有可执行步骤。请先添加接口用例或流程控制步骤。', { exact: true })).toBeVisible();
  });

  test('删除确认框以正常的居中弹窗显示', async ({ page }) => {
    await page.goto('/#/scenarios');
    await page.getByRole('button', { name: '更多', exact: true }).click();
    await page.getByRole('menuitem', { name: '删除场景', exact: true }).click();

    const dialog = page.locator('.el-message-box');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('确定要彻底删除该场景及其所有关联记录吗？此操作不可逆！', { exact: true })).toBeVisible();
    const box = await dialog.boundingBox();
    expect(box).not.toBeNull();
    expect(box.width).toBeGreaterThan(300);
    expect(box.width).toBeLessThan(620);
    expect(box.x).toBeGreaterThan(200);
  });
});
