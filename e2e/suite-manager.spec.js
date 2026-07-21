const { test, expect } = require('@playwright/test');
const { login } = require('./helpers/auth');

const suite = {
  id: 1,
  name: '核心回归套件',
  description: '覆盖登录到下单的关键链路',
  env_id: 7,
  case_count: 2,
  last_status: 'failed',
  last_run_at: '2026-07-22T02:03:04Z',
  scenarios: [
    { scenario_id: 11, case_name: '登录并提交订单', active: true, method: 'POST', url: '/orders', sort_order: 0 },
    { scenario_id: 12, case_name: '查询订单状态', active: true, method: 'GET', url: '/orders/1', sort_order: 1 },
  ],
};

const execution = {
  execution_id: 'exec-20260722-001',
  suite_id: 1,
  status: 'failed',
  trigger: 'webhook',
  attempt: 2,
  total_cases: 2,
  passed_cases: 1,
  failed_cases: 1,
  cancelled_cases: 0,
  duration_ms: 1834,
  queued_at: '2026-07-22T02:03:00Z',
  started_at: '2026-07-22T02:03:01Z',
  finished_at: '2026-07-22T02:03:03Z',
  case_results: [
    { scenario_id: 11, case_name: '登录并提交订单', status: 'passed', duration_ms: 620, error: null },
    { scenario_id: 12, case_name: '查询订单状态', status: 'failed', duration_ms: 1214, error: '响应状态断言失败' },
  ],
};

async function installSuiteApiMocks(page) {
  const state = {
    schedulePayload: null,
    schedule: null,
    webhooks: [],
  };
  const json = (route, body, status = 200) => route.fulfill({
    status,
    contentType: 'application/json; charset=utf-8',
    body: JSON.stringify(body),
  });

  await page.route('**/api/auto-test/environments**', route => json(route, [
    { id: 7, name: '预发布环境', is_default: true },
  ]));
  await page.route('**/api/auto-test/scenarios**', route => json(route, {
    items: [
      { id: 11, name: '登录并提交订单' },
      { id: 12, name: '查询订单状态' },
    ],
  }));
  await page.route(/\/api\/auto-test\/webhooks(?:\/|\?|$)/, async route => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    if (url.pathname === '/api/auto-test/webhooks' && method === 'GET') {
      return json(route, { items: state.webhooks, total: state.webhooks.length });
    }
    if (url.pathname === '/api/auto-test/webhooks' && method === 'POST') {
      const payload = request.postDataJSON();
      const created = {
        id: 'wh-001',
        suite_id: payload.suite_id,
        name: payload.name,
        is_active: true,
        allowed_clock_skew_seconds: payload.allowed_clock_skew_seconds,
        inbound_url: '/api/auto-test/webhooks/inbound/wh-001',
        status_url_template: '/api/auto-test/webhooks/inbound/wh-001/executions/{execution_id}',
        signing_secret: 'e2e-one-time-signing-secret',
        signature_headers: {
          algorithm: 'HMAC-SHA256',
          timestamp: 'X-TestMaster-Timestamp',
          signature: 'X-TestMaster-Signature',
          event_id: 'X-TestMaster-Event-ID',
        },
      };
      state.webhooks = [{ ...created, signing_secret: undefined }];
      return json(route, created, 201);
    }
    if (url.pathname === '/api/auto-test/webhooks/wh-001' && method === 'PATCH') {
      state.webhooks[0].is_active = request.postDataJSON().is_active;
      return json(route, state.webhooks[0]);
    }
    if (url.pathname.endsWith('/rotate-secret') && method === 'POST') {
      return json(route, { ...state.webhooks[0], signing_secret: 'rotated-e2e-secret' });
    }
    return json(route, { detail: `Unexpected Webhook request: ${method} ${url.pathname}` }, 500);
  });
  await page.route(/\/api\/auto-test\/suites(?:\/|\?|$)/, async route => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const path = url.pathname;
    if (path === '/api/auto-test/suites' && method === 'GET') {
      return json(route, { list: [suite], total: 1, page: 1, size: 20 });
    }
    if (path === '/api/auto-test/suites/1/schedule' && method === 'GET') {
      return json(route, { schedule: state.schedule });
    }
    if (path === '/api/auto-test/suites/1/schedule' && method === 'PUT') {
      state.schedulePayload = request.postDataJSON();
      state.schedule = {
        ...state.schedulePayload,
        id: 21,
        suite_id: 1,
        next_run_at: '2026-07-23T00:00:00Z',
        last_enqueued_at: null,
        notification_config: state.schedulePayload.notification_config || {},
      };
      return json(route, { schedule: state.schedule });
    }
    if (path === '/api/auto-test/suites/1/runs' && method === 'GET') {
      return json(route, { runs: [execution], total: 1 });
    }
    if (path === `/api/auto-test/suites/executions/${execution.execution_id}/events` && method === 'GET') {
      return json(route, { events: [
        { sequence: 1, type: 'execution_queued', level: 'info', payload: { trigger: 'webhook' }, created_at: '2026-07-22T02:03:00Z' },
        { sequence: 2, type: 'assertion_failed', level: 'error', payload: { scenario_id: 12 }, created_at: '2026-07-22T02:03:03Z' },
      ] });
    }
    if (path === `/api/auto-test/suites/executions/${execution.execution_id}` && method === 'GET') {
      return json(route, execution);
    }
    if (path === '/api/auto-test/suites/1' && method === 'GET') {
      return json(route, suite);
    }
    return json(route, { detail: `Unexpected suite request: ${method} ${path}` }, 500);
  });
  return state;
}

function suiteRow(page) {
  return page.locator('.el-table__row').filter({ hasText: suite.name }).first();
}

test.describe('接口回归套件核心工作流', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('保存服务端定时策略并保留执行策略字段', async ({ page }) => {
    const state = await installSuiteApiMocks(page);
    await page.goto('/#/suites');
    await expect(page.getByRole('heading', { name: '测试套件管理' })).toBeVisible({ timeout: 10000 });

    await suiteRow(page).getByRole('button', { name: '定时', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: '服务端定时执行' });
    await expect(dialog).toBeVisible();
    const cronInput = dialog.locator('.el-form-item')
      .filter({ hasText: 'Cron 表达式' })
      .locator('input');
    await cronInput.fill('0 8 * * 1-5');
    await dialog.getByRole('button', { name: '保存', exact: true }).click();

    await expect(page.getByText('定时配置已保存', { exact: true })).toBeVisible();
    expect(state.schedulePayload).toMatchObject({
      cron_expression: '0 8 * * 1-5',
      timezone_name: 'Asia/Shanghai',
      env_id: 7,
      misfire_policy: 'coalesce',
      max_concurrent: 1,
      execution_timeout_seconds: 1800,
      max_retries: 0,
      is_active: true,
    });
    await expect(dialog.getByText('下次执行', { exact: true })).toBeVisible();
  });

  test('创建 Webhook 后展示一次性密钥与完整接入信息', async ({ page }) => {
    await installSuiteApiMocks(page);
    await page.goto('/#/suites');

    await suiteRow(page).getByRole('button', { name: 'Webhook', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: '外部触发 Webhook' });
    await expect(dialog).toBeVisible();
    const nameInput = dialog.locator('.el-form-item').filter({ hasText: '名称' }).locator('input').first();
    await nameInput.fill('主干流水线回归');
    await dialog.getByRole('button', { name: '创建', exact: true }).click();

    await expect(dialog.getByText('新签名密钥（仅本次显示）', { exact: true })).toBeVisible();
    await expect(dialog.locator('.secret-alert input')).toHaveValue('e2e-one-time-signing-secret');
    await expect(dialog.getByText('主干流水线回归', { exact: true })).toBeVisible();
    await dialog.getByRole('button', { name: '接入信息', exact: true }).click();

    const integration = page.getByRole('dialog', { name: 'Webhook 接入信息' });
    await expect(integration).toBeVisible();
    await expect(integration.getByText('HMAC-SHA256', { exact: true })).toBeVisible();
    await expect(integration.locator('input').first()).toHaveValue(/\/api\/auto-test\/webhooks\/inbound\/wh-001$/);
    await expect(integration.getByText('X-TestMaster-Event-ID', { exact: true })).toBeVisible();
  });

  test('从历史记录查看 Webhook 触发来源、失败详情和执行事件', async ({ page }) => {
    await installSuiteApiMocks(page);
    await page.goto('/#/suites');

    await suiteRow(page).getByRole('button', { name: '记录', exact: true }).click();
    const history = page.getByRole('dialog', { name: `${suite.name} · 执行记录` });
    await expect(history).toBeVisible();
    await expect(history.getByText(execution.execution_id, { exact: true })).toBeVisible();
    await expect(history.getByText('Webhook', { exact: true })).toBeVisible();
    await expect(history.getByText('失败', { exact: true })).toBeVisible();
    await history.getByRole('button', { name: '详情', exact: true }).click();

    const result = page.getByRole('dialog', { name: '执行结果' });
    await expect(result).toBeVisible();
    await expect(result.getByText('查询订单状态', { exact: true })).toBeVisible();
    await expect(result.getByText('响应状态断言失败', { exact: true })).toBeVisible();
    await expect(result.getByText('assertion_failed', { exact: true })).toBeVisible();
    await expect(result.getByText(/"scenario_id":12/)).toBeVisible();
  });
});
