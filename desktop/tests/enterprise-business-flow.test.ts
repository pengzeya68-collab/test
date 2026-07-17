import { afterEach, expect, it } from 'vitest';
import { createServer, Server } from 'http';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { CaseExecutionEngine } from '../src/worker/execution-engine';

let server: Server | null = null;
afterEach(async () => { if (server) { server.closeAllConnections?.(); await new Promise<void>(resolve => server!.close(() => resolve())); } server = null; });

const locator = (strategy: any, value: string, framePath: string[] = []) => ({ strategy, value, options: {}, fallbacks: [], framePath });
const step = (id: string, type: string, target: any = null, input: any = null) => ({
  id, order: 10, name: id, type, enabled: true, breakpoint: false, locator: target, input,
  timeout_ms: 5000, retry: { count: 1, delay_ms: 50 }, continue_on_failure: false,
  screenshot: 'on-failure' as const, condition: null, children: [],
});

it('runs a complete login-to-order enterprise workflow', async () => {
  const uploadFile = path.join(os.tmpdir(), 'testmaster-enterprise-attachment.txt');
  fs.writeFileSync(uploadFile, 'enterprise attachment', 'utf8');
  server = createServer((req, res) => {
    const url = req.url || '/';
    res.setHeader('content-type', 'text/html; charset=utf-8');
    if (url === '/login') {
      res.end('<title>登录</title><form action="/dashboard"><label>用户名<input data-testid="username" name="username"></label><label>密码<input data-testid="password" type="password" name="password"></label><button data-testid="login">登录</button></form>');
      return;
    }
    if (url.startsWith('/dashboard')) {
      res.end('<title>业务工作台</title><h1 data-testid="welcome">欢迎进入企业工作台</h1><iframe id="checkout" src="/checkout"></iframe><button data-testid="pay" onclick="window.open(\'/payment\')">打开支付</button><a data-testid="receipt" href="/receipt" download>下载订单凭证</a><script>console.log("dashboard-ready")</script>');
      return;
    }
    if (url === '/checkout') {
      res.end('<label>地址<input data-testid="address"></label><input data-testid="attachment" type="file"><div data-testid="notes" contenteditable="true"></div><button data-testid="place-order" onclick="result.textContent=\'ORDER-1001 下单成功\'">提交订单</button><div data-testid="result" id="result"></div>');
      return;
    }
    if (url === '/payment') {
      res.end('<title>订单支付</title><h1>支付订单 ORDER-1001</h1>');
      return;
    }
    if (url === '/receipt') {
      res.setHeader('content-type', 'text/plain; charset=utf-8');
      res.setHeader('content-disposition', 'attachment; filename="order-1001.txt"');
      res.end('ORDER-1001 receipt verified');
      return;
    }
    res.statusCode = 404; res.end('not found');
  });
  await new Promise<void>(resolve => server!.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + (server.address() as any).port;
  const frame = ['#checkout'];
  const events: any[] = [];
  const steps = [
    step('open-login', 'goto', null, { url: '/login' }),
    step('username', 'fill', locator('test_id', 'username'), { value: 'enterprise-user' }),
    step('password', 'fill', locator('test_id', 'password'), { value: 'secret-password', secret: true }),
    step('login', 'click', locator('test_id', 'login')),
    step('dashboard-url', 'wait_for_url', null, { url: '**/dashboard?**' }),
    step('welcome', 'assert_text_contains', locator('test_id', 'welcome'), { expected: '企业工作台' }),
    step('address', 'fill', locator('test_id', 'address', frame), { value: '香港中环 100 号' }),
    step('upload', 'upload_file', locator('test_id', 'attachment', frame), { paths: [uploadFile] }),
    step('notes', 'fill', locator('test_id', 'notes', frame), { value: '企业采购订单备注' }),
    step('order', 'click', locator('test_id', 'place-order', frame)),
    step('order-result', 'assert_text_contains', locator('test_id', 'result', frame), { expected: 'ORDER-1001 下单成功' }),
    step('extract-order', 'extract_text', locator('test_id', 'result', frame), { name: 'orderResult' }),
    step('pay', 'click', locator('test_id', 'pay')),
    step('switch-payment', 'switch_page', null, { index: 'last' }),
    step('payment-title', 'assert_title', null, { expected: '订单支付' }),
    step('close-payment', 'close_page'),
    step('download-receipt', 'download', locator('test_id', 'receipt'), { expectedFilename: '^order-1001\\.txt$', minBytes: 10, containsText: 'ORDER-1001 receipt verified', variable: 'receiptPath' }),
  ];
  const result = await new CaseExecutionEngine().execute({
    case_id: 996, name: 'enterprise login to order', base_url: origin,
    default_timeout_ms: 5000, navigation_timeout_ms: 5000, steps,
  }, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: true }, event => events.push(event));
  expect(result.status, JSON.stringify(result)).toBe('passed');
  expect(result.passedSteps).toBe(steps.length);
  expect(result.tracePath).toBeNull();
  expect(events.some(event => event.type === 'console' && event.text === 'dashboard-ready')).toBeTruthy();
});


