import { chromium } from 'playwright';
import { createServer } from 'http';

const server = createServer((req, res) => {
  res.setHeader('content-type', 'text/html; charset=utf-8');
  if (req.url === '/login') {
    res.setHeader('set-cookie', 'session=enterprise-user; Path=/; SameSite=Lax');
    res.end('<script>localStorage.setItem("accessToken","saved-token");document.body.textContent="登录完成"</script>');
  } else if (req.url === '/force-login') {
    res.end('<title>login</title><input type="password" name="password">');
  } else {
    const authenticated = String(req.headers.cookie || '').includes('session=enterprise-user');
    res.end("<title>" + (authenticated ? "authenticated" : "login-required") + "</title><body><script>document.body.textContent=document.cookie+'|'+localStorage.getItem('accessToken')</script></body>");
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = 'http://127.0.0.1:' + server.address().port;
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let savedId = null;
let caseId = null;
try {
  const page = browser.contexts()[0].pages()[0];
  caseId = await page.evaluate(async () => {
    const response = await fetch('http://127.0.0.1:5001/api/ui-automation/cases', { method: 'POST', headers: { Authorization: 'Bearer ' + localStorage.getItem('token'), 'Content-Type': 'application/json' }, body: JSON.stringify({ name: '验证码登录态验收-' + Date.now(), base_url: 'http://example.test/login' }) });
    if (!response.ok) throw new Error('CREATE_CASE_' + response.status + ':' + await response.text());
    return (await response.json()).id;
  });
  await page.evaluate(id => { location.hash = '#/ui-automation/cases/' + id; }, caseId);
  await page.getByText('人工登录并保存', { exact: true }).waitFor({ timeout: 15000 });
  const result = await page.evaluate(async ({ origin }) => {
    await window.testmaster.recorder.start({ url: origin + '/login', slowMo: 0 });
    await new Promise(resolve => setTimeout(resolve, 700));
    const saved = await window.testmaster.authStates.saveCurrent('自动验收登录态');
    await window.testmaster.recorder.stop();
    const states = await window.testmaster.authStates.list();
    const refreshEvents = [];
    await window.testmaster.recorder.start({ url: origin + '/account', slowMo: 0, authStateId: saved.id }, event => refreshEvents.push(event));
    await new Promise(resolve => setTimeout(resolve, 700));
    const refreshed = await window.testmaster.authStates.saveCurrent('自动验收登录态', saved.id);
    await window.testmaster.recorder.stop();
    const ready = refreshEvents.find(event => event.type === 'ready');
    const snapshot = {
      case_id: 99992, name: 'auth-state-acceptance', base_url: origin,
      default_timeout_ms: 5000, navigation_timeout_ms: 5000,
      steps: [
        { id: 'open', order: 10, name: '进入业务页', type: 'goto', enabled: true, breakpoint: false, locator: null, input: { url: '/account' }, timeout_ms: 5000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'never', condition: null, children: [] },
        { id: 'assert', order: 20, name: '验证登录态', type: 'assert_text_contains', enabled: true, breakpoint: false, locator: { strategy: 'css', value: 'body', options: {}, fallbacks: [], framePath: [] }, input: { expected: 'session=enterprise-user|saved-token' }, timeout_ms: 5000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'never', condition: null, children: [] },
      ],
    };
    const { promise } = window.testmaster.execution.runCase(snapshot, { headless: true, authStateId: saved.id, traceOnFailure: false, screenshotsOnFailure: false });
    const run = await promise;
    const validCheck = await window.testmaster.authStates.validate(saved.id, origin + '/account');
    const invalidCheck = await window.testmaster.authStates.validate(saved.id, origin + '/force-login');
    return { saved, refreshed, listed: states.some(item => item.id === saved.id), refreshAuthenticated: ready?.title === 'authenticated', validCheck, invalidCheck, run };
  }, { origin });
  savedId = result.saved.id;
  if (!result.listed || !result.refreshAuthenticated || result.refreshed.id !== result.saved.id || result.validCheck.valid !== true || result.invalidCheck.valid !== false || result.run.status !== 'passed') throw new Error(JSON.stringify(result));
  await page.evaluate(async ({ caseId, origin }) => {
    const response = await fetch('http://127.0.0.1:5001/api/ui-automation/cases/' + caseId + '/steps', {
      method: 'PUT', headers: { Authorization: 'Bearer ' + localStorage.getItem('token'), 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps: [
        { id: crypto.randomUUID(), order: 10, name: '进入登录后页面', type: 'goto', enabled: true, breakpoint: false, locator: null, input: { url: origin + '/account' }, timeout_ms: 5000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'never', condition: null, children: [] },
        { id: crypto.randomUUID(), order: 20, name: '验证复用登录态', type: 'assert_text_contains', enabled: true, breakpoint: false, locator: { strategy: 'css', value: 'body', options: {}, fallbacks: [], framePath: [] }, input: { expected: 'session=enterprise-user|saved-token' }, timeout_ms: 5000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'never', condition: null, children: [] },
      ] }),
    });
    if (!response.ok) throw new Error('SAVE_UI_FLOW_' + response.status + ':' + await response.text());
  }, { caseId, origin });
  await page.reload();
  await page.getByText('人工登录并保存', { exact: true }).waitFor({ timeout: 15000 });
  await page.locator('.case-context .el-select').nth(1).click();
  await page.locator('.el-select-dropdown:visible').getByText('自动验收登录态', { exact: true }).click();
  await page.getByRole('button', { name: '运行完整流程' }).click();
  await page.getByText('运行结束：通过', { exact: false }).waitFor({ timeout: 45000 });
  console.log(JSON.stringify({ passed: true, encryptedProfileListed: result.listed, oldStateLoadedForRefresh: result.refreshAuthenticated, overwrittenInPlace: result.refreshed.id === result.saved.id, validPreflight: result.validCheck.valid, invalidPreflightBlocked: !result.invalidCheck.valid, playbackStatus: result.run.status, uiSelectedProfileRun: 'passed' }));
} finally {
  const page = browser.contexts()[0].pages()[0];
  if (savedId) await page.evaluate(id => window.testmaster.authStates.delete(id), savedId).catch(() => {});
  if (caseId) await page.evaluate(async id => { await fetch('http://127.0.0.1:5001/api/ui-automation/cases/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } }); }, caseId).catch(() => {});
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}

