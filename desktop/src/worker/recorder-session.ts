import { Browser, BrowserContext, BrowserContextOptions, Page, chromium } from 'playwright';
import { bundledChromiumExecutable } from './browser-runtime';
import { randomUUID } from 'crypto';
import { Locator as TestMasterLocator } from '../shared/contracts/locator';

export type RecorderMode = 'record' | 'assert-visible' | 'assert-text';
export type RecorderEvent =
  | { type: 'ready'; sessionId: string; url: string; title: string }
  | { type: 'action'; step: Record<string, unknown>; replaceLast?: boolean; insertBeforeLast?: boolean }
  | { type: 'mode'; mode: RecorderMode }
  | { type: 'console'; level: string; text: string; url: string }
  | { type: 'network'; method: string; url: string; status: number; failed: boolean }
  | { type: 'page'; url: string; title: string }
  | { type: 'error'; message: string };

export interface RecorderStartOptions {
  url: string;
  viewport?: { width: number; height: number } | null;
  slowMo?: number;
  storageState?: BrowserContextOptions['storageState'] | null;
}

const RECORDER_SCRIPT = `
(() => {
  if (window.__testmasterRecorderInstalled) return;
  window.__testmasterRecorderInstalled = true;
  window.__testmasterRecorderMode = 'record';
  let inputTimer = null;

  const clean = value => String(value || '').replace(/\\s+/g, ' ').trim().slice(0, 500);
  const cssEscape = value => window.CSS && CSS.escape ? CSS.escape(value) : String(value).replace(/[^a-zA-Z0-9_-]/g, '\\\\$&');
  const roleOf = el => {
    const explicit = el.getAttribute('role');
    if (explicit) return explicit;
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute('type') || '').toLowerCase();
    if (tag === 'button') return 'button';
    if (tag === 'a' && el.hasAttribute('href')) return 'link';
    if (tag === 'select') return 'combobox';
    if (tag === 'textarea') return 'textbox';
    if (tag === 'input' && ['button', 'submit', 'reset'].includes(type)) return 'button';
    if (tag === 'input' && type === 'checkbox') return 'checkbox';
    if (tag === 'input' && type === 'radio') return 'radio';
    if (tag === 'input') return 'textbox';
    return '';
  };
  const accessibleName = el => clean(el.getAttribute('aria-label') || el.getAttribute('title') || el.innerText || el.value || '');
  const labelText = el => {
    if (el.id) {
      const label = document.querySelector('label[for="' + cssEscape(el.id) + '"]');
      if (label) return clean(label.innerText);
    }
    const parent = el.closest('label');
    return parent ? clean(parent.innerText) : '';
  };
  const cssPath = el => {
    if (el.id && !/\\d{5,}/.test(el.id)) return '#' + cssEscape(el.id);
    const name = el.getAttribute('name');
    if (name) return el.tagName.toLowerCase() + '[name="' + String(name).replace(/"/g, '\\\\"') + '"]';
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && parts.length < 5) {
      let part = node.tagName.toLowerCase();
      const parent = node.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(x => x.tagName === node.tagName);
        if (siblings.length > 1) part += ':nth-of-type(' + (siblings.indexOf(node) + 1) + ')';
      }
      parts.unshift(part);
      node = parent;
      if (node === document.body) { parts.unshift('body'); break; }
    }
    return parts.join(' > ');
  };
  const locatorFor = el => {
    const candidates = [];
    for (const attr of ['data-testid', 'data-test', 'data-qa']) {
      const value = clean(el.getAttribute(attr));
      if (value) candidates.push({ strategy: 'test_id', value, options: {}, fallbacks: [], framePath: [] });
    }
    const label = labelText(el);
    if (label) candidates.push({ strategy: 'label', value: label, options: {}, fallbacks: [], framePath: [] });
    const placeholder = clean(el.getAttribute('placeholder'));
    if (placeholder) candidates.push({ strategy: 'placeholder', value: placeholder, options: {}, fallbacks: [], framePath: [] });
    const role = roleOf(el);
    const name = accessibleName(el);
    if (role && name) candidates.push({ strategy: 'role', value: role, options: { name }, fallbacks: [], framePath: [] });
    if (name && ['button', 'a'].includes(el.tagName.toLowerCase())) candidates.push({ strategy: 'text', value: name, options: { exact: true }, fallbacks: [], framePath: [] });
    candidates.push({ strategy: 'css', value: cssPath(el), options: {}, fallbacks: [], framePath: [] });
    const primary = candidates[0];
    primary.fallbacks = candidates.slice(1, 4);
    return primary;
  };
  const send = payload => window.__testmasterRecord(payload).catch(() => {});
  const step = (type, name, locator, input) => ({
    id: (crypto.randomUUID ? crypto.randomUUID() : 'step-' + Date.now() + '-' + Math.random().toString(16).slice(2)), order: Date.now(), name, type, enabled: true, breakpoint: false,
    locator: locator || null, input: input == null ? null : input, timeout_ms: null,
    retry: { count: 0, delay_ms: 0 }, continue_on_failure: false,
    screenshot: 'on-failure', condition: null, children: []
  });
  const targetElement = event => event.target && event.target.nodeType === 1 ? event.target.closest('button,a,input,textarea,select,[role],[contenteditable="true"]') || event.target : null;

  document.addEventListener('click', event => {
    const el = targetElement(event);
    if (!el) return;
    const locator = locatorFor(el);
    const mode = window.__testmasterRecorderMode || 'record';
    if (mode !== 'record') {
      event.preventDefault(); event.stopImmediatePropagation();
      const text = clean(el.innerText || el.value || '');
      send({ kind: 'assertion', step: step(mode === 'assert-text' ? 'assert_text_contains' : 'assert_visible', mode === 'assert-text' ? '检查包含文字' : '检查元素可见', locator, mode === 'assert-text' ? { expected: text } : null) });
      window.__testmasterRecorderMode = 'record';
      send({ kind: 'mode', mode: 'record' });
      return;
    }
    const tag = el.tagName.toLowerCase();
    const inputType = (el.getAttribute('type') || '').toLowerCase();
    if (tag === 'input' && ['checkbox', 'radio'].includes(inputType)) {
      send({ kind: 'action', step: step(el.checked ? 'check' : 'uncheck', el.checked ? '勾选' : '取消勾选', locator, null) });
      return;
    }
    if (['input', 'textarea', 'select'].includes(tag)) return;
    send({ kind: 'action', step: step('click', '点击' + (accessibleName(el) ? '“' + accessibleName(el).slice(0, 40) + '”' : '元素'), locator, null) });
  }, true);

  document.addEventListener('input', event => {
    const el = targetElement(event);
    if (!el || (!['input', 'textarea'].includes(el.tagName.toLowerCase()) && !el.isContentEditable)) return;
    clearTimeout(inputTimer);
    inputTimer = setTimeout(() => {
      const secret = (el.getAttribute('type') || '').toLowerCase() === 'password';
      send({ kind: 'action', replaceLast: true, step: step('fill', '输入' + (labelText(el) || el.getAttribute('placeholder') || '内容'), locatorFor(el), { value: secret ? '{{PASSWORD}}' : (el.isContentEditable ? el.innerText : el.value), secret }) });
    }, 350);
  }, true);

  document.addEventListener('change', event => {
    const el = targetElement(event);
    if (!el) return;
    if (el.tagName.toLowerCase() === 'select') {
      send({ kind: 'action', step: step('select_option', '选择下拉项', locatorFor(el), { value: el.value }) });
      return;
    }
    if (el.tagName.toLowerCase() === 'input' && (el.getAttribute('type') || '').toLowerCase() === 'file') {
      const names = Array.from(el.files || []).map(file => file.name);
      send({ kind: 'action', step: step('upload_file', '上传文件', locatorFor(el), { paths: [], filenames: names, requiresFileSelection: true }) });
    }
  }, true);
})();
`;

export class RecorderSession {
  readonly id = randomUUID();
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private pages = new Set<Page>();
  private mode: RecorderMode = 'record';

  constructor(private readonly onEvent: (event: RecorderEvent) => void) {}

  async start(options: RecorderStartOptions): Promise<{ sessionId: string; browserVersion: string }> {
    if (!/^https?:\/\//i.test(options.url) && !options.url.startsWith('data:')) throw new Error('INVALID_RECORDER_URL');
    this.browser = await chromium.launch({ headless: false, slowMo: options.slowMo ?? 0, executablePath: bundledChromiumExecutable() });
    this.context = await this.browser.newContext({
      viewport: options.viewport ?? { width: 1365, height: 768 },
      storageState: options.storageState ?? undefined,
    });
    await this.context.exposeBinding('__testmasterRecord', async (source, payload: any) => this.handleBrowserEvent(payload, source.frame));
    await this.context.addInitScript(RECORDER_SCRIPT);
    this.context.on('page', page => void this.attachPage(page));
    const page = await this.context.newPage();
    await this.attachPage(page);
    await page.goto(options.url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    this.emitAction('goto', '打开网页', null, { url: options.url });
    this.onEvent({ type: 'ready', sessionId: this.id, url: page.url(), title: await page.title() });
    return { sessionId: this.id, browserVersion: this.browser.version() };
  }

  async setMode(mode: RecorderMode): Promise<void> {
    this.mode = mode;
    await Promise.all([...this.pages].filter(page => !page.isClosed()).map(page => page.evaluate(value => { (window as any).__testmasterRecorderMode = value; }, mode).catch(() => {})));
    this.onEvent({ type: 'mode', mode });
  }

  async validateLocator(locator: TestMasterLocator): Promise<{ count: number; preview: string }> {
    const page = [...this.pages].reverse().find(candidate => !candidate.isClosed());
    if (!page) throw new Error('RECORDER_PAGE_NOT_FOUND');
    const target = this.resolveLocator(page, locator);
    const count = await target.count();
    if (count > 0) {
      await target.evaluateAll((elements) => {
        for (const element of elements) {
          const html = element as HTMLElement;
          const previous = html.style.outline;
          html.style.outline = '3px solid #e5484d';
          html.style.outlineOffset = '2px';
          setTimeout(() => { html.style.outline = previous; html.style.outlineOffset = ''; }, 1800);
        }
      });
    }
    const preview = count > 0 ? await target.first().evaluate(element => (element as HTMLElement).innerText || element.getAttribute('aria-label') || element.tagName) : '';
    return { count, preview: String(preview).trim().slice(0, 200) };
  }

  private resolveLocator(page: Page, locator: TestMasterLocator): import('playwright').Locator {
    let scope: any = page;
    for (const selector of locator.framePath || []) scope = scope.frameLocator(selector);
    switch (locator.strategy) {
      case 'test_id': return scope.getByTestId(locator.value);
      case 'role': return scope.getByRole(locator.value as any, locator.options as any);
      case 'label': return scope.getByLabel(locator.value, locator.options as any);
      case 'placeholder': return scope.getByPlaceholder(locator.value, locator.options as any);
      case 'text': return scope.getByText(locator.value, locator.options as any);
      case 'css': return scope.locator(locator.value);
      case 'xpath': return scope.locator(`xpath=${locator.value}`);
      default: throw new Error('INVALID_LOCATOR_STRATEGY');
    }
  }
  async getStorageState(): Promise<object> {
    if (!this.context) throw new Error('RECORDER_NOT_RUNNING');
    return this.context.storageState();
  }

  async getCurrentPageInfo(): Promise<{ url: string; title: string }> {
    const page = [...this.pages].reverse().find(item => !item.isClosed());
    if (!page) throw new Error('RECORDER_PAGE_NOT_AVAILABLE');
    return { url: page.url(), title: await page.title().catch(() => '') };
  }

  async stop(): Promise<void> {
    await this.context?.close().catch(() => {});
    await this.browser?.close().catch(() => {});
    this.pages.clear(); this.context = null; this.browser = null;
  }

  private async attachPage(page: Page): Promise<void> {
    if (this.pages.has(page)) return;
    const additionalPage = this.pages.size > 0;
    this.pages.add(page);
    if (additionalPage) this.emitAction('switch_page', '切换到新页面', null, { index: 'last' });
    page.on('console', message => this.onEvent({ type: 'console', level: message.type(), text: message.text(), url: page.url() }));
    page.on('response', response => { if (response.status() >= 400) this.onEvent({ type: 'network', method: response.request().method(), url: response.url(), status: response.status(), failed: true }); });
    page.on('requestfailed', request => this.onEvent({ type: 'network', method: request.method(), url: request.url(), status: 0, failed: true }));
    page.on('framenavigated', async frame => { if (frame === page.mainFrame()) this.onEvent({ type: 'page', url: page.url(), title: await page.title().catch(() => '') }); });
    page.on('dialog', dialog => {
      this.onEvent({ type: 'action', insertBeforeLast: true, step: this.makeStep('accept_dialog', '自动确认弹窗', null, { message: dialog.message(), dialogType: dialog.type() }) });
      void dialog.accept().catch(() => {});
    });
    page.on('close', () => this.pages.delete(page));
    await page.evaluate(RECORDER_SCRIPT).catch(() => {});
    await page.evaluate(value => { (window as any).__testmasterRecorderMode = value; }, this.mode).catch(() => {});
  }

  private async handleBrowserEvent(payload: any, frame?: import('playwright').Frame): Promise<void> {
    if ((payload?.kind === 'action' || payload?.kind === 'assertion') && payload.step) {
      const framePath = frame ? await this.getFramePath(frame) : [];
      if (payload.step.locator) {
        payload.step.locator.framePath = framePath;
        for (const fallback of payload.step.locator.fallbacks || []) fallback.framePath = framePath;
      }
      this.onEvent({ type: 'action', step: payload.step, replaceLast: !!payload.replaceLast });
    }
    if (payload?.kind === 'mode') { this.mode = payload.mode; this.onEvent({ type: 'mode', mode: payload.mode }); }
  }

  private async getFramePath(frame: import('playwright').Frame): Promise<string[]> {
    const selectors: string[] = [];
    let current: import('playwright').Frame | null = frame;
    while (current?.parentFrame()) {
      const element = await current.frameElement();
      const selector = await element.evaluate((node: Element) => {
        const id = node.getAttribute('id');
        if (id) return '#' + CSS.escape(id);
        const name = node.getAttribute('name');
        if (name) return `iframe[name="${CSS.escape(name)}"]`;
        const testId = node.getAttribute('data-testid');
        if (testId) return `iframe[data-testid="${CSS.escape(testId)}"]`;
        const frames = Array.from(node.parentElement?.querySelectorAll(':scope > iframe') || []);
        return `iframe:nth-of-type(${Math.max(0, frames.indexOf(node as HTMLIFrameElement)) + 1})`;
      });
      selectors.unshift(selector);
      current = current.parentFrame();
    }
    return selectors;
  }

  private makeStep(type: string, name: string, locator: unknown, input: unknown): Record<string, unknown> {
    return { id: randomUUID(), order: Date.now(), name, type, enabled: true, breakpoint: false, locator, input, timeout_ms: null, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false, screenshot: 'on-failure', condition: null, children: [] };
  }

  private emitAction(type: string, name: string, locator: unknown, input: unknown): void {
    this.onEvent({ type: 'action', step: this.makeStep(type, name, locator, input) });
  }
}








