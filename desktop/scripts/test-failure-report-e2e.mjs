import { chromium } from 'playwright';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let caseId = null;
try {
  const page = browser.contexts()[0].pages()[0];
  await page.waitForTimeout(1200);
  const created = await page.evaluate(async () => {
    const token = localStorage.getItem('token');
    const headers = { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' };
    const base = 'http://127.0.0.1:5001/api/ui-automation';
    const request = async (path, options = {}) => {
      const response = await fetch(base + path, { ...options, headers });
      if (!response.ok) throw new Error(path + ':' + response.status + ':' + await response.text());
      return response.json();
    };
    const testCase = await request('/cases', { method: 'POST', body: JSON.stringify({ name: 'Trace报告自动验收-' + Date.now(), base_url: null }) });
    const locator = { strategy: 'test_id', value: 'missing-button', options: {}, fallbacks: [], framePath: [] };
    const common = { enabled: true, breakpoint: false, timeout_ms: 400, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'on-failure', condition: null, children: [] };
    await request('/cases/' + testCase.id + '/steps', { method: 'PUT', body: JSON.stringify({ steps: [
      { ...common, id: 'open', order: 10, name: '打开页面', type: 'goto', locator: null, input: { url: 'data:text/html,<h1>Trace acceptance</h1>' } },
      { ...common, id: 'fail', order: 20, name: '触发失败', type: 'click', locator, input: null },
    ] }) });
    return testCase;
  });
  caseId = created.id;
  await page.evaluate(id => { location.hash = '#/ui-automation/cases/' + id; }, caseId);
  await page.getByText('用户操作流程', { exact: true }).waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: '运行完整流程' }).click();
  await page.getByText('运行结束：失败', { exact: false }).waitFor({ timeout: 30000 });
  await page.waitForTimeout(2500);
  const report = await page.evaluate(async caseId => {
    const token = localStorage.getItem('token');
    const headers = { Authorization: 'Bearer ' + token };
    const base = 'http://127.0.0.1:5001/api/ui-automation';
    const runs = await (await fetch(base + '/runs?case_id=' + caseId, { headers })).json();
    const run = runs.items[0];
    const artifacts = await (await fetch(base + '/runs/' + run.id + '/artifacts', { headers })).json();
    return { run, artifacts: artifacts.items };
  }, caseId);
  const types = report.artifacts.map(item => item.type);
  if (report.run.status !== 'failed' || !types.includes('screenshot') || !types.includes('trace')) throw new Error('REPORT_INCOMPLETE_' + JSON.stringify({ status: report.run.status, types }));
  console.log(JSON.stringify({ passed: true, status: report.run.status, artifactTypes: types, traceStored: report.artifacts.find(item => item.type === 'trace').storage_path }));
} finally {
  if (caseId) {
    const page = browser.contexts()[0].pages()[0];
    await page.evaluate(async id => {
      const token = localStorage.getItem('token');
      await fetch('http://127.0.0.1:5001/api/ui-automation/cases/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } });
    }, caseId).catch(() => {});
  }
  await browser.close();
}
