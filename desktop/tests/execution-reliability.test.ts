import { it, expect } from 'vitest';
import * as fs from 'fs';
import { CaseExecutionEngine } from '../src/worker/execution-engine';

const locator = (strategy: any, value: string, fallbacks: any[] = []) => ({
  strategy, value, options: {}, fallbacks, framePath: [],
});

const step = (id: string, type: string, target: any = null, input: any = null, overrides: any = {}) => ({
  id, order: 10, name: id, type, enabled: true, breakpoint: false, locator: target, input,
  timeout_ms: 1000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false,
  screenshot: 'on-failure' as const, condition: null, children: [], ...overrides,
});

const snapshot = (steps: any[]) => ({
  case_id: 991, name: 'reliability', base_url: null, default_timeout_ms: 1000,
  navigation_timeout_ms: 5000, steps,
});

it('uses recorded fallback locator when primary locator is stale', async () => {
  const target = locator('test_id', 'stale-id', [locator('role', 'button')]);
  target.fallbacks[0].options = { name: '提交订单' };
  const url = 'data:text/html,%3Cmeta%20charset%3D%22utf-8%22%3E%3Cbutton%20onclick%3D%22this.textContent%3D%26quot%3B%E5%B7%B2%E6%8F%90%E4%BA%A4%26quot%3B%22%3E%E6%8F%90%E4%BA%A4%E8%AE%A2%E5%8D%95%3C%2Fbutton%3E';
  const result = await new CaseExecutionEngine().execute(snapshot([
    step('open', 'goto', null, { url }),
    step('click', 'click', target),
    step('assert', 'assert_text_equals', locator('role', 'button'), { expected: '已提交' }),
  ]), null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false }, () => {});
  expect(result.status, JSON.stringify(result)).toBe('passed');
});

it('retries a transiently unavailable element and emits retry log', async () => {
  const events: any[] = [];
  const html = '<script>setTimeout(()=>document.body.innerHTML=\'<button data-testid="late">继续</button>\',450)</script>';
  const result = await new CaseExecutionEngine().execute(snapshot([
    step('open', 'goto', null, { url: 'data:text/html,' + encodeURIComponent(html) }),
    step('late', 'click', locator('test_id', 'late'), null, { timeout_ms: 250, retry: { count: 2, delay_ms: 100 } }),
  ]), null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false }, event => events.push(event));
  expect(result.status).toBe('passed');
  expect(events.some(event => event.type === 'log' && event.level === 'warn')).toBeTruthy();
});

it('always screenshot stores an artifact and successful trace is discarded', async () => {
  const events: any[] = [];
  const result = await new CaseExecutionEngine().execute(snapshot([
    step('open', 'goto', null, { url: 'data:text/html,<h1>完成</h1>' }, { screenshot: 'always' }),
  ]), null, { headless: true, screenshotsOnFailure: true, traceOnFailure: true }, event => events.push(event));
  expect(result.status).toBe('passed');
  expect(result.stepResults[0].screenshotPath).toBeTruthy();
  expect(fs.existsSync(result.stepResults[0].screenshotPath!)).toBeTruthy();
  expect(events.some(event => event.type === 'log' && String(event.message).startsWith('Trace saved:'))).toBeFalsy();
});







it('returns a readable trace artifact for failed runs only', async () => {
  const events: any[] = [];
  const result = await new CaseExecutionEngine().execute(snapshot([
    step('open', 'goto', null, { url: 'data:text/html,<h1>failure</h1>' }),
    step('missing', 'click', locator('test_id', 'never-exists'), null, { timeout_ms: 300 }),
  ]), null, { headless: true, screenshotsOnFailure: false, traceOnFailure: true }, event => events.push(event));
  expect(result.status).toBe('failed');
  expect(result.tracePath).toBeTruthy();
  expect(fs.existsSync(result.tracePath!)).toBeTruthy();
  expect(events.some(event => event.type === 'log' && String(event.message).startsWith('Trace saved:'))).toBeTruthy();
});

