import { afterEach, expect, it } from 'vitest';
import { createServer, Server } from 'http';
import { CaseExecutionEngine } from '../src/worker/execution-engine';

let server: Server | null = null;
afterEach(async () => { if (server) await new Promise<void>(resolve => server!.close(() => resolve())); server = null; });

const step = (id: string, type: string, locator: any = null, input: any = null) => ({
  id, order: 10, name: id, type, enabled: true, breakpoint: false, locator, input,
  timeout_ms: 3000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false,
  screenshot: 'never' as const, condition: null, children: [],
});
const loc = (strategy: any, value: string) => ({ strategy, value, options: {}, fallbacks: [], framePath: [] });

it('restores cookies and localStorage before the first page opens', async () => {
  server = createServer((_req, res) => {
    res.setHeader('content-type', 'text/html; charset=utf-8');
    res.end('<body><script>document.body.textContent=document.cookie+"|"+localStorage.getItem("accessToken")</script></body>');
  });
  await new Promise<void>(resolve => server!.listen(0, '127.0.0.1', resolve));
  const address = server.address() as any;
  const origin = 'http://127.0.0.1:' + address.port;
  const storageState = {
    cookies: [{ name: 'session', value: 'ok', domain: '127.0.0.1', path: '/', expires: -1, httpOnly: false, secure: false, sameSite: 'Lax' }],
    origins: [{ origin, localStorage: [{ name: 'accessToken', value: 'token-ok' }] }],
  };
  const result = await new CaseExecutionEngine().execute({
    case_id: 992, name: 'auth reuse', base_url: origin, default_timeout_ms: 3000, navigation_timeout_ms: 3000,
    steps: [step('open', 'goto', null, { url: '/' }), step('check', 'assert_text_contains', loc('css', 'body'), { expected: 'session=ok|token-ok' })],
  }, null, { headless: true, screenshotsOnFailure: false, traceOnFailure: false, storageState }, () => {});
  expect(result.status, JSON.stringify(result)).toBe('passed');
});

it('redacts secret environment variables in debugger snapshots', async () => {
  const engine = new CaseExecutionEngine();
  let pausedVariables: Record<string, string> | null = null;
  const resultPromise = engine.execute({
    case_id: 993, name: 'secret redaction', base_url: null, default_timeout_ms: 3000, navigation_timeout_ms: 3000,
    steps: [step('open', 'goto', null, { url: 'data:text/html,ok' })],
  }, { baseUrl: '', variables: { PASSWORD: 'raw-secret', USERNAME: 'tester' }, secretKeys: ['PASSWORD'] },
  { headless: true, screenshotsOnFailure: false, traceOnFailure: false, debugMode: true }, event => {
    if (event.type === 'run:paused') { pausedVariables = event.variables; engine.resume('continue'); }
  });
  const result = await resultPromise;
  expect(result.status).toBe('passed');
  expect(pausedVariables).toEqual({ PASSWORD: '******', USERNAME: 'tester' });
});


it('captures browser console, HTTP failures and paused page context', async () => {
  server = createServer((req, res) => {
    if (req.url === '/fail') { res.statusCode = 503; res.end('failed'); return; }
    res.setHeader('content-type', 'text/html; charset=utf-8');
    res.end('<title>诊断页面</title><script>console.error("browser-diagnostic");fetch("/fail")</script>');
  });
  await new Promise<void>(resolve => server!.listen(0, '127.0.0.1', resolve));
  const address = server.address() as any;
  const origin = 'http://127.0.0.1:' + address.port;
  const events: any[] = [];
  const engine = new CaseExecutionEngine();
  const result = await engine.execute({
    case_id: 995, name: 'diagnostics', base_url: origin, default_timeout_ms: 3000, navigation_timeout_ms: 3000,
    steps: [
      step('open', 'goto', null, { url: '/' }),
      { ...step('wait', 'wait_for_timeout', null, { ms: 300 }), breakpoint: true },
    ],
  }, null, { headless: true, screenshotsOnFailure: false, traceOnFailure: false }, event => {
    events.push(event);
    if (event.type === 'run:paused') engine.resume('continue');
  });
  expect(result.status).toBe('passed');
  expect(events.some(event => event.type === 'console' && event.text === 'browser-diagnostic')).toBeTruthy();
  expect(events.some(event => event.type === 'network' && event.status === 503)).toBeTruthy();
  const paused = events.find(event => event.type === 'run:paused');
  expect(paused.url).toBe(origin + '/');
  expect(paused.title).toBe('诊断页面');
  expect(paused.screenshotPath).toBeTruthy();
});

