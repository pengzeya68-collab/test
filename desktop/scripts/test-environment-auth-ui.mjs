import { chromium } from 'playwright';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
try {
  const page = browser.contexts()[0].pages()[0];
  await page.evaluate(() => { location.hash = '#/ui-automation/cases/2'; });
  await page.getByText('测试环境', { exact: true }).waitFor({ timeout: 15000 });
  const body = await page.locator('body').innerText();
  for (const text of ['测试环境', '登录态', '每次重新登录', '地址与超时']) {
    if (!body.includes(text)) throw new Error('MISSING_CONTROL_' + text);
  }
  const bridge = await page.evaluate(async () => ({
    hasAuthStates: typeof window.testmaster?.authStates?.list === 'function',
    authStates: await window.testmaster.authStates.list(),
    token: localStorage.getItem('token'),
  }));
  if (!bridge.hasAuthStates) throw new Error('AUTH_STATE_BRIDGE_MISSING');
  if (!bridge.token) throw new Error('LOGIN_TOKEN_MISSING');

  const runResult = await page.evaluate(async () => {
    const snapshot = {
      case_id: 99991, name: 'runtime-config-acceptance', base_url: null,
      default_timeout_ms: 3000, navigation_timeout_ms: 3000,
      steps: [{
        id: 'open', order: 10, name: '打开验收页', type: 'goto', enabled: true,
        breakpoint: false, locator: null, input: { url: 'data:text/html,<h1>runtime-ok</h1>' },
        timeout_ms: 3000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false,
        screenshot: 'never', condition: null, children: [],
      }],
    };
    const { promise } = window.testmaster.execution.runCase(snapshot, {
      headless: true, traceOnFailure: false, screenshotsOnFailure: false,
      runtimeConfigRequest: { serverUrl: 'http://127.0.0.1:5001', token: localStorage.getItem('token'), environmentId: null },
    });
    return promise;
  });
  if (runResult.status !== 'passed') throw new Error('RUNTIME_CONFIG_RUN_FAILED_' + JSON.stringify(runResult));
  await page.screenshot({ path: 'environment-auth-acceptance.png', fullPage: true });
  console.log(JSON.stringify({ passed: true, controls: true, authStateBridge: true, storedProfiles: bridge.authStates.length, runtimeConfigRun: runResult.status }));
} finally {
  await browser.close();
}

