import { chromium } from 'playwright';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let caseId = null;
try {
  const page = browser.contexts()[0].pages()[0];
  await page.waitForTimeout(1200);
  const setup = await page.evaluate(async () => {
    const headers = { Authorization: 'Bearer ' + localStorage.getItem('token'), 'Content-Type': 'application/json' };
    const base = 'http://127.0.0.1:5001/api/ui-automation';
    const req = async (path, options = {}) => { const r = await fetch(base + path, { ...options, headers }); if (!r.ok) throw new Error(path + ':' + r.status + ':' + await r.text()); return r.json(); };
    const name = '历史报告界面验收-' + Date.now();
    const c = await req('/cases', { method: 'POST', body: JSON.stringify({ name }) });
    const id = 'history-' + crypto.randomUUID();
    await req('/cases/' + c.id + '/steps', { method: 'PUT', body: JSON.stringify({ steps: [{ id, order: 10, type: 'goto', name: '打开页面', input: { url: 'https://example.com' } }] }) });
    const version = await req('/cases/' + c.id + '/versions', { method: 'POST', body: '{}' });
    const run = await req('/runs', { method: 'POST', body: JSON.stringify({ case_id: c.id, case_version_id: version.id }) });
    await req('/runs/' + run.id + '/events', { method: 'POST', body: JSON.stringify({ events: [{ sequence: 1, type: 'run:start', totalSteps: 1 }, { sequence: 2, type: 'step:start', stepId: id }, { sequence: 3, type: 'step:pass', stepId: id, durationMs: 10 }, { sequence: 4, type: 'run:finish', status: 'passed', passedSteps: 1, failedSteps: 0 }] }) });
    await req('/runs/' + run.id + '/artifacts/upload', { method: 'POST', body: JSON.stringify({ type: 'screenshot', filename: 'history.png', mime_type: 'image/png', content_base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nEAAAAAASUVORK5CYII=' }) });
    await req('/runs/' + run.id + '/artifacts/upload', { method: 'POST', body: JSON.stringify({ type: 'trace', filename: 'history-trace.zip', mime_type: 'application/zip', content_base64: 'emlwLWNvbnRlbnQ=' }) });
    return { caseId: c.id, name };
  });
  caseId = setup.caseId;
  await page.evaluate(() => { location.hash = '#/ui-automation/cases'; });
  await page.reload();
  const row = page.getByRole('row').filter({ hasText: setup.name });
  await row.waitFor({ timeout: 15000 });
  await row.getByRole('button', { name: '运行记录' }).click();
  await page.getByText('步骤结果', { exact: true }).waitFor({ timeout: 10000 });
  await page.getByRole('tab', { name: '产物' }).click();
  await page.getByText('history.png', { exact: true }).waitFor({ timeout: 10000 });
  const screenshotRow = page.getByRole('row').filter({ hasText: 'history.png' });
  await screenshotRow.getByRole('button', { name: '查看' }).click();
  await page.getByRole('dialog', { name: 'history.png' }).waitFor({ timeout: 10000 });
  const imageVisible = await page.getByRole('dialog', { name: 'history.png' }).locator('img').isVisible();
  await page.getByRole('dialog', { name: 'history.png' }).getByRole('button', { name: 'Close' }).click().catch(async () => { await page.keyboard.press('Escape'); });
  const traceRow = page.getByRole('row').filter({ hasText: 'history-trace.zip' });
  const downloadPromise = page.waitForEvent('download', { timeout: 10000 });
  await traceRow.getByRole('button', { name: '保存' }).click();
  const download = await downloadPromise;
  if (!imageVisible || download.suggestedFilename() !== 'history-trace.zip') throw new Error('HISTORY_ARTIFACT_UI_FAILED');
  console.log(JSON.stringify({ passed: true, screenshotViewed: imageVisible, traceFilename: download.suggestedFilename() }));
} finally {
  if (caseId) { const page = browser.contexts()[0].pages()[0]; await page.evaluate(async id => { await fetch('http://127.0.0.1:5001/api/ui-automation/cases/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } }); }, caseId).catch(() => {}); }
  await browser.close();
}

