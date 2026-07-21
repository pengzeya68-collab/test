/**
 * Playwright step execution engine.
 *
 * Executes a sequence of UI automation steps using Playwright,
 * streaming events back to the renderer in real time.
 *
 * Per Section 9 (Execution Semantics):
 *   - Each case iteration gets a new BrowserContext by default.
 *   - Action default timeout: 10s, Assertion default: 5s, Navigation: 30s.
 *   - Cleanup runs in finally, even after cancellation.
 *   - Screenshot on failure, trace on failure.
 */

import { Browser, BrowserContext, Page, chromium } from 'playwright';
import { bundledChromiumExecutable } from './browser-runtime';
import { expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { Locator } from '../shared/contracts/locator';
import { StepSnapshot } from '../shared/contracts/steps';

// ------------------------------------------------------------------
// Types
// ------------------------------------------------------------------

export interface CaseSnapshot {
  case_id: number;
  name: string;
  base_url: string | null;
  default_timeout_ms: number;
  navigation_timeout_ms: number;
  steps: StepSnapshot[];
}

export interface EnvironmentConfig {
  baseUrl: string;
  variables: Record<string, string>;
  secretKeys?: string[];
}

export interface RunOptions {
  headless: boolean;
  screenshotsOnFailure: boolean;
  traceOnFailure: boolean;
  videoOnFailure?: boolean;
  debugMode?: boolean;
  storageState?: object | null;
  artifactRootDir?: string;
}

export interface StepResult {
  stepId: string;
  status: 'passed' | 'failed' | 'skipped' | 'cancelled';
  durationMs: number;
  error: string | null;
  screenshotPath: string | null;
}

export interface RunResult {
  status: 'passed' | 'failed' | 'cancelled' | 'infra_error';
  totalSteps: number;
  passedSteps: number;
  failedSteps: number;
  durationMs: number;
  stepResults: StepResult[];
  tracePath: string | null;
  videoPath: string | null;
}

export type StepEvent =
  | { type: 'step:start'; stepId: string; stepName: string; stepType: string }
  | { type: 'step:pass'; stepId: string; durationMs: number }
  | { type: 'step:fail'; stepId: string; durationMs: number; error: string; screenshotPath?: string }
  | { type: 'step:skip'; stepId: string; reason: string }
  | { type: 'run:start'; totalSteps: number }
  | { type: 'run:finish'; status: string; passedSteps: number; failedSteps: number; durationMs: number }
  | { type: 'run:paused'; stepId: string; stepName: string; stepType: string; variables: Record<string, string>; url: string; title: string; screenshotPath: string | null }
  | { type: 'run:resumed'; mode: 'continue' | 'step' }
  | { type: 'console'; level: string; text: string; url: string }
  | { type: 'network'; method: string; url: string; status: number; failed: boolean; error?: string }
  | { type: 'log'; level: string; message: string };

export type StepEventCallback = (event: StepEvent) => void;

const WINDOWS_RESERVED_NAME = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$/i;

export function safeArtifactFilename(value: string, fallback = 'artifact'): string {
  const leaf = path.win32.basename(String(value || '').replace(/\//g, '\\'));
  let cleaned = leaf
    .replace(/[\u0000-\u001f\u007f<>:"/\\|?*]/g, '_')
    .replace(/[. ]+$/g, '')
    .trim();
  if (!cleaned || cleaned === '.' || cleaned === '..') cleaned = fallback;
  if (WINDOWS_RESERVED_NAME.test(cleaned)) cleaned = `_${cleaned}`;
  if (cleaned.length > 180) {
    const extension = path.extname(cleaned).slice(0, 20);
    cleaned = `${cleaned.slice(0, Math.max(1, 180 - extension.length))}${extension}`;
  }
  return cleaned;
}

export function uniqueArtifactPath(rootDir: string, requestedFilename: string, fallback = 'artifact'): string {
  const root = path.resolve(rootDir);
  fs.mkdirSync(root, { recursive: true });
  const safeName = safeArtifactFilename(requestedFilename, fallback);
  const extension = path.extname(safeName);
  const stem = path.basename(safeName, extension);
  for (let index = 0; index < 10_000; index += 1) {
    const name = index === 0 ? safeName : `${stem}-${index}${extension}`;
    const candidate = path.resolve(root, name);
    if (candidate !== root && candidate.startsWith(`${root}${path.sep}`) && !fs.existsSync(candidate)) return candidate;
  }
  throw new Error('ARTIFACT_FILENAME_EXHAUSTED');
}

// ------------------------------------------------------------------
// Execution engine
// ------------------------------------------------------------------

export class CaseExecutionEngine {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  private cancelled = false;
  private variables: Record<string, string> = {};
  private secretKeys = new Set<string>();
  private diagnosticPages = new WeakSet<Page>();
  private pauseMode: 'breakpoints' | 'every-step' = 'breakpoints';
  private pauseRequested = false;
  private paused = false;
  private resumeResolver: (() => void) | null = null;
  private artifactRootDir = path.join(os.tmpdir(), 'testmaster-artifacts');

  /**
   * Execute a case snapshot.
   *
   * @param snapshot  The immutable case version snapshot
   * @param env       Optional environment configuration
   * @param options   Run options (headless, screenshots, trace)
   * @param onEvent   Callback for streaming events
   */
  async execute(
    snapshot: CaseSnapshot,
    env: EnvironmentConfig | null,
    options: RunOptions,
    onEvent: StepEventCallback
  ): Promise<RunResult> {
    const startTime = Date.now();
    const stepResults: StepResult[] = [];
    let passedSteps = 0;
    let failedSteps = 0;
    let savedTracePath: string | null = null;
    let savedVideoPath: string | null = null;
    let infrastructureError: unknown = null;
    let currentVideo: import('playwright').Video | null = null;

    this.pauseMode = options.debugMode ? 'every-step' : 'breakpoints';
    this.artifactRootDir = path.resolve(options.artifactRootDir || path.join(os.tmpdir(), 'testmaster-artifacts'));
    onEvent({ type: 'run:start', totalSteps: snapshot.steps.length });

    try {
      // Launch browser
      this.browser = await chromium.launch({ headless: options.headless, executablePath: bundledChromiumExecutable() });
      const videoDir = path.join(this.artifactRootDir, 'videos');
      if (options.videoOnFailure && !fs.existsSync(videoDir)) fs.mkdirSync(videoDir, { recursive: true });
      this.context = await this.browser.newContext({
        viewport: { width: 1280, height: 720 },
        storageState: options.storageState as any || undefined,
        recordVideo: options.videoOnFailure ? { dir: videoDir, size: { width: 1280, height: 720 } } : undefined,
      });

      // Enable tracing if requested
      if (options.traceOnFailure) {
        await this.context.tracing.start({
          screenshots: true,
          snapshots: true,
          sources: true,
        });
      }

      this.context.on('page', diagnosticPage => this.attachPageDiagnostics(diagnosticPage, onEvent));
      this.page = await this.context.newPage();
      currentVideo = this.page.video();
      this.attachPageDiagnostics(this.page, onEvent);

      // Set default timeouts
      this.page.setDefaultTimeout(snapshot.default_timeout_ms || 10000);
      this.page.setDefaultNavigationTimeout(snapshot.navigation_timeout_ms || 30000);

      // Resolve base URL
      const baseUrl = env?.baseUrl || snapshot.base_url || '';
      this.variables = { ...(env?.variables || {}) };
      this.secretKeys = new Set(env?.secretKeys || []);

      // Execute steps
      for (const step of snapshot.steps) {
        if (this.cancelled) {
          stepResults.push({
            stepId: step.id,
            status: 'cancelled',
            durationMs: 0,
            error: null,
            screenshotPath: null,
          });
          continue;
        }

        if (!step.enabled) {
          onEvent({ type: 'step:skip', stepId: step.id, reason: '步骤已停用' });
          stepResults.push({
            stepId: step.id,
            status: 'skipped',
            durationMs: 0,
            error: null,
            screenshotPath: null,
          });
          continue;
        }

        if (this.pauseRequested || this.pauseMode === 'every-step' || (this.pauseMode === 'breakpoints' && step.breakpoint)) {
          await this.waitForResume(step, onEvent);
          if (this.cancelled) continue;
        }

        onEvent({
          type: 'step:start',
          stepId: step.id,
          stepName: step.name || step.type,
          stepType: step.type,
        });

        const stepStart = Date.now();
        try {
          await this.executeStepWithRetry(step, baseUrl, step.timeout_ms || snapshot.default_timeout_ms || 10000, onEvent);
          const duration = Date.now() - stepStart;
          const screenshotPath = step.screenshot === 'always' ? await this.captureScreenshot(step.id, 'pass') : null;
          passedSteps++;
          onEvent({ type: 'step:pass', stepId: step.id, durationMs: duration });
          stepResults.push({
            stepId: step.id,
            status: 'passed',
            durationMs: duration,
            error: null,
            screenshotPath,
          });
        } catch (error: any) {
          const duration = Date.now() - stepStart;
          if (this.cancelled) {
            const duration = Date.now() - stepStart;
            stepResults.push({
              stepId: step.id,
              status: 'cancelled',
              durationMs: duration,
              error: null,
              screenshotPath: null,
            });
            onEvent({ type: 'step:skip', stepId: step.id, reason: '运行已取消' });
            continue;
          }

          failedSteps++;

          // Take screenshot on failure
          let screenshotPath: string | null = null;
          if (step.screenshot !== 'never' && (step.screenshot === 'always' || options.screenshotsOnFailure)) {
            screenshotPath = await this.captureScreenshot(step.id, 'fail');
          }

          onEvent({
            type: 'step:fail',
            stepId: step.id,
            durationMs: duration,
            error: error?.message || String(error),
            screenshotPath: screenshotPath || undefined,
          });

          stepResults.push({
            stepId: step.id,
            status: 'failed',
            durationMs: duration,
            error: error?.message || String(error),
            screenshotPath,
          });

          // If continue_on_failure is false, stop execution
          if (!step.continue_on_failure) {
            // Mark remaining steps as skipped
            const remainingIdx = snapshot.steps.indexOf(step);
            for (let i = remainingIdx + 1; i < snapshot.steps.length; i++) {
              onEvent({
                type: 'step:skip',
                stepId: snapshot.steps[i].id,
                reason: '前置步骤失败',
              });
              stepResults.push({
                stepId: snapshot.steps[i].id,
                status: 'skipped',
                durationMs: 0,
                error: null,
                screenshotPath: null,
              });
            }
            break;
          }
        }
      }
    } catch (error: any) {
      onEvent({ type: 'log', level: 'error', message: `Run error: ${error?.message}` });
      infrastructureError = error;
    } finally {
      // Save trace on failure
      if (options.traceOnFailure && this.context) {
        try {
          if (failedSteps > 0 || infrastructureError) {
            const dir = path.join(this.artifactRootDir, 'traces');
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            const tracePath = uniqueArtifactPath(dir, `trace-${safeArtifactFilename(String(snapshot.case_id), 'case')}-${Date.now()}.zip`, 'trace.zip');
            savedTracePath = tracePath;
            await this.context.tracing.stop({ path: tracePath });
            onEvent({ type: 'log', level: 'info', message: `Trace saved: ${tracePath}` });
          } else {
            await this.context.tracing.stop();
          }
        } catch (e) {
          // Trace save failure is not fatal
        }
      }

      // Playwright only guarantees the final video path after its context closes.
      await this.cleanup();
      if (currentVideo) {
        try {
          const videoPath = await currentVideo.path();
          if ((failedSteps > 0 || infrastructureError) && options.videoOnFailure) {
            savedVideoPath = videoPath;
            onEvent({ type: 'log', level: 'info', message: `Video saved: ${videoPath}` });
          } else if (videoPath && fs.existsSync(videoPath)) {
            fs.unlinkSync(videoPath);
          }
        } catch {
          // Artifact capture failure must not replace the original test result.
        }
      }
    }

    const status: RunResult['status'] = infrastructureError
      ? 'infra_error'
      : this.cancelled ? 'cancelled' : failedSteps > 0 ? 'failed' : 'passed';

    const result: RunResult = {
      status,
      totalSteps: snapshot.steps.length,
      passedSteps,
      failedSteps,
      durationMs: Date.now() - startTime,
      stepResults,
      tracePath: savedTracePath,
      videoPath: savedVideoPath,
    };

    onEvent({
      type: 'run:finish',
      status,
      passedSteps,
      failedSteps,
      durationMs: result.durationMs,
    });

    return result;
  }

  /**
   * Cancel the current execution.
   * Idempotent 鈥?safe to call multiple times.
   */
  async cancel(): Promise<void> {
    this.cancelled = true;
    this.resumeResolver?.();
    this.resumeResolver = null;
    await this.cleanup();
  }

  pause(): void {
    this.pauseRequested = true;
  }

  resume(mode: 'continue' | 'step' = 'continue'): void {
    this.pauseMode = mode === 'step' ? 'every-step' : 'breakpoints';
    this.pauseRequested = false;
    this.paused = false;
    this.resumeResolver?.();
    this.resumeResolver = null;
  }

  isPaused(): boolean { return this.paused; }

  private async waitForResume(step: StepSnapshot, onEvent: StepEventCallback): Promise<void> {
    this.paused = true;
    this.pauseRequested = false;
    const resumePromise = new Promise<void>(resolve => { this.resumeResolver = resolve; });
    const screenshotPath = await this.captureScreenshot(step.id, 'pass');
    onEvent({ type: 'run:paused', stepId: step.id, stepName: step.name || step.type, stepType: step.type, variables: Object.fromEntries(Object.entries(this.variables).map(([key, value]) => [key, this.secretKeys.has(key) ? '******' : value])), url: this.page?.url() || '', title: await this.page?.title().catch(() => '') || '', screenshotPath });
    await resumePromise;
  }

  // ------------------------------------------------------------------
  // Step execution
  // ------------------------------------------------------------------

  private async executeStepWithRetry(
    step: StepSnapshot,
    baseUrl: string,
    timeoutMs: number,
    onEvent: StepEventCallback
  ): Promise<void> {
    const retryCount = Math.max(0, Number(step.retry?.count || 0));
    const retryDelay = Math.max(0, Number(step.retry?.delay_ms || 0));
    let lastError: unknown;
    for (let attempt = 0; attempt <= retryCount; attempt++) {
      try {
        await this.executeStep(step, baseUrl, timeoutMs);
        return;
      } catch (error) {
        lastError = error;
        if (attempt >= retryCount || this.cancelled) break;
        onEvent({ type: 'log', level: 'warn', message: '步骤失败，正在进行第 ' + (attempt + 1) + ' 次重试：' + (step.name || step.type) });
        if (retryDelay > 0) await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
    throw lastError;
  }
  private async executeStep(step: StepSnapshot, baseUrl: string, timeoutMs: number): Promise<void> {
    const page = this.page!;
    const input = step.input || {};
    const resolvedInput = this.resolveVariablesInInput(input);

    switch (step.type) {
      // Navigation
      case 'goto': {
        const url = this.resolveUrl(resolvedInput.url || '', baseUrl);
        await page.goto(url, { timeout: timeoutMs, waitUntil: 'load' });
        break;
      }
      case 'reload':
        await page.reload({ timeout: timeoutMs });
        break;
      case 'go_back':
        await page.goBack({ timeout: timeoutMs });
        break;
      case 'switch_page': {
        const pages = this.context?.pages() || [];
        const index = resolvedInput.index === 'last' || resolvedInput.index == null ? pages.length - 1 : Number(resolvedInput.index);
        if (!pages[index]) throw new Error('TARGET_PAGE_NOT_FOUND');
        this.page = pages[index];
        await this.page.bringToFront();
        break;
      }
      case 'close_page': {
        const pages = this.context?.pages() || [];
        if (pages.length <= 1) throw new Error('CANNOT_CLOSE_LAST_PAGE');
        await page.close();
        this.page = pages.find(candidate => !candidate.isClosed()) || null;
        await this.page?.bringToFront();
        break;
      }
      case 'set_viewport':
        await page.setViewportSize({ width: Number(resolvedInput.width || 1280), height: Number(resolvedInput.height || 720) });
        break;
      case 'accept_dialog':
        page.once('dialog', dialog => void dialog.accept(resolvedInput.promptText).catch(() => {}));
        break;
      case 'dismiss_dialog':
        page.once('dialog', dialog => void dialog.dismiss().catch(() => {}));
        break;

      // Element operations
      case 'click': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.click({ timeout: timeoutMs });
        break;
      }
      case 'double_click': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.dblclick({ timeout: timeoutMs });
        break;
      }
      case 'fill': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.fill(resolvedInput.value || '', { timeout: timeoutMs });
        break;
      }
      case 'type': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.pressSequentially(resolvedInput.value || '', { timeout: timeoutMs, delay: Number(resolvedInput.delay_ms || 0) });
        break;
      }      case 'clear': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.clear({ timeout: timeoutMs });
        break;
      }
      case 'press': {
        if (step.locator) {
          const locator = await this.resolveLocatorWithFallback(page, step.locator, timeoutMs);
          await locator.press(resolvedInput.key || 'Enter', { timeout: timeoutMs });
        } else {
          await page.keyboard.press(resolvedInput.key || 'Enter');
        }
        break;
      }
      case 'hover': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.hover({ timeout: timeoutMs });
        break;
      }
      case 'focus': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.focus({ timeout: timeoutMs });
        break;
      }
      case 'check': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.check({ timeout: timeoutMs });
        break;
      }
      case 'uncheck': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.uncheck({ timeout: timeoutMs });
        break;
      }
      case 'select_option': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.selectOption(resolvedInput.value || '', { timeout: timeoutMs });
        break;
      }
      case 'drag_and_drop': {
        const source = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        if (!resolvedInput.targetLocator) throw new Error('DRAG_TARGET_NOT_CONFIGURED');
        const target = await this.resolveLocatorWithFallback(page, resolvedInput.targetLocator, timeoutMs);
        await source.dragTo(target, { timeout: timeoutMs });
        break;
      }      case 'upload_file': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        const paths = Array.isArray(resolvedInput.paths) ? resolvedInput.paths : [resolvedInput.path].filter(Boolean);
        if (!paths.length) throw new Error('UPLOAD_FILE_NOT_CONFIGURED');
        await locator.setInputFiles(paths, { timeout: timeoutMs });
        break;
      }
      case 'download': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        const [download] = await Promise.all([
          page.waitForEvent('download', { timeout: timeoutMs }),
          locator.click({ timeout: timeoutMs }),
        ]);
        const dir = path.join(this.artifactRootDir, 'downloads');
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        const filename = safeArtifactFilename(download.suggestedFilename(), 'download');
        const savedPath = uniqueArtifactPath(dir, filename, 'download');
        await download.saveAs(savedPath);
        if (resolvedInput.expectedFilename && !(new RegExp(resolvedInput.expectedFilename).test(filename))) {
          throw new Error('DOWNLOAD_FILENAME_MISMATCH: ' + filename);
        }
        const size = fs.statSync(savedPath).size;
        if (resolvedInput.minBytes != null && size < Number(resolvedInput.minBytes)) {
          throw new Error('DOWNLOAD_TOO_SMALL: ' + size);
        }
        if (resolvedInput.containsText) {
          const content = fs.readFileSync(savedPath, 'utf8');
          if (!content.includes(String(resolvedInput.containsText))) throw new Error('DOWNLOAD_CONTENT_MISMATCH');
        }
        this.variables[resolvedInput.variable || 'downloadPath'] = savedPath;
        break;
      }
      case 'scroll_into_view': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.scrollIntoViewIfNeeded({ timeout: timeoutMs });
        break;
      }

      // Waits
      case 'wait_for_element': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.waitFor({ state: 'visible', timeout: timeoutMs });
        break;
      }
      case 'wait_for_load_state':
        await page.waitForLoadState(resolvedInput.state || 'load', { timeout: timeoutMs });
        break;
      case 'wait_for_url':
        await page.waitForURL(resolvedInput.url || '**', { timeout: timeoutMs });
        break;
      case 'wait_for_timeout':
        await page.waitForTimeout(resolvedInput.ms || 1000);
        break;

      // Assertions 鈥?use shorter default (5s per spec)
      case 'assert_visible': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.waitFor({ state: 'visible', timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_hidden': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await locator.waitFor({ state: 'hidden', timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_enabled': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toBeEnabled({ timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_disabled': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toBeDisabled({ timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_editable': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toBeEditable({ timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_checked': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toBeChecked({ timeout: Math.min(timeoutMs, 5000) });
        break;
      }      case 'assert_text_equals': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toHaveText(resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_text_contains': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toContainText(resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_text_matches': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toHaveText(new RegExp(resolvedInput.expected || '', resolvedInput.flags || ''), { timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_value': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toHaveValue(resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_attribute': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toHaveAttribute(resolvedInput.name || '', resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_css_property': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toHaveCSS(resolvedInput.name || '', resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;
      }
      case 'assert_element_count': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        await expect(locator).toHaveCount(Number(resolvedInput.expected || 0), { timeout: Math.min(timeoutMs, 5000) });
        break;
      }      case 'assert_url':
        await expect(page).toHaveURL(resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;
      case 'assert_title':
        await expect(page).toHaveTitle(resolvedInput.expected || '', { timeout: Math.min(timeoutMs, 5000) });
        break;

      // Variables
      case 'set_variable':
        this.variables[resolvedInput.name || ''] = resolvedInput.value || '';
        break;
      case 'extract_value': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        this.variables[resolvedInput.name || 'extracted'] = await locator.inputValue({ timeout: timeoutMs });
        break;
      }
      case 'extract_attribute': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        this.variables[resolvedInput.name || 'extracted'] = await locator.getAttribute(resolvedInput.attribute || '') || '';
        break;
      }
      case 'extract_url':
        this.variables[resolvedInput.name || 'currentUrl'] = page.url();
        break;      case 'extract_text': {
        const locator = await this.resolveLocatorWithFallback(page, step.locator!, timeoutMs);
        const text = await locator.textContent({ timeout: timeoutMs });
        this.variables[resolvedInput.name || 'extracted'] = text || '';
        break;
      }

      default:
        throw new Error(`Unsupported step type: ${step.type}`);
    }
  }

  // ------------------------------------------------------------------
  // Locator resolution
  // ------------------------------------------------------------------

  private async resolveLocatorWithFallback(page: Page, loc: Locator, timeoutMs: number): Promise<import('playwright').Locator> {
    const candidates = [loc, ...(loc.fallbacks || [])];
    const probeTimeout = Math.max(250, Math.min(1500, Math.floor(timeoutMs / candidates.length)));
    const errors: string[] = [];
    for (const candidate of candidates) {
      const locator = this.resolveLocator(page, { ...candidate, framePath: candidate.framePath?.length ? candidate.framePath : loc.framePath });
      try {
        await locator.first().waitFor({ state: 'attached', timeout: probeTimeout });
        if (await locator.count() > 0) return locator;
      } catch (error: any) {
        errors.push(candidate.strategy + '=' + candidate.value + ': ' + (error?.message || error));
      }
    }
    throw new Error('LOCATOR_NOT_FOUND: ' + candidates.map(item => item.strategy + '=' + item.value).join(' -> ') + '\n' + errors.join('\n'));
  }
  private resolveLocator(page: Page, loc: Locator): import('playwright').Locator {
    let target: Page | import('playwright').FrameLocator = page;

    // Handle frame path
    if (loc.framePath && loc.framePath.length > 0) {
      for (const selector of loc.framePath) {
        target = (target as any).frameLocator(selector);
      }
    }

    switch (loc.strategy) {
      case 'test_id':
        return (target as any).getByTestId(loc.value, loc.options);
      case 'role':
        return (target as any).getByRole(loc.value, loc.options);
      case 'label':
        return (target as any).getByLabel(loc.value, loc.options);
      case 'placeholder':
        return (target as any).getByPlaceholder(loc.value, loc.options);
      case 'text':
        return (target as any).getByText(loc.value, loc.options);
      case 'css':
        return target.locator(loc.value);
      case 'xpath':
        return target.locator(`xpath=${loc.value}`);
      default:
        throw new Error(`Unknown locator strategy: ${loc.strategy}`);
    }
  }

  // ------------------------------------------------------------------
  // Variable resolution
  // ------------------------------------------------------------------

  private resolveVariablesInInput(input: any): any {
    if (typeof input === 'string') {
      return this.resolveString(input);
    }
    if (input && typeof input === 'object') {
      const result: any = Array.isArray(input) ? [] : {};
      for (const key of Object.keys(input)) {
        result[key] = this.resolveVariablesInInput(input[key]);
      }
      return result;
    }
    return input;
  }

  private resolveString(str: string): string {
    return str.replace(/\{\{(\w+)\}\}/g, (_, name) => this.variables[name] ?? '');
  }

  private resolveUrl(url: string, baseUrl: string): string {
    const resolved = this.resolveString(url);
    if (resolved.startsWith('http://') || resolved.startsWith('https://')) {
      return resolved;
    }
    if (baseUrl && !resolved.startsWith('http')) {
      return baseUrl.replace(/\/$/, '') + '/' + resolved.replace(/^\//, '');
    }
    return resolved;
  }

  // ------------------------------------------------------------------
  // Cleanup
  // ------------------------------------------------------------------

  private redactSecrets(value: string): string {
    let output = String(value || '');
    for (const key of this.secretKeys) {
      const secret = this.variables[key];
      if (secret) output = output.split(secret).join('******');
    }
    return output;
  }

  private sanitizeUrl(value: string): string {
    try {
      const url = new URL(value);
      for (const key of [...url.searchParams.keys()]) {
        if (/(password|passwd|secret|token|api[_-]?key)/i.test(key)) url.searchParams.set(key, '******');
      }
      return this.redactSecrets(url.toString());
    } catch {
      return this.redactSecrets(value);
    }
  }
  private attachPageDiagnostics(page: Page, onEvent: StepEventCallback): void {
    if (this.diagnosticPages.has(page)) return;
    this.diagnosticPages.add(page);
    page.on('console', message => onEvent({ type: 'console', level: message.type(), text: this.redactSecrets(message.text()), url: this.sanitizeUrl(page.url()) }));
    page.on('response', response => {
      if (response.status() >= 400) onEvent({ type: 'network', method: response.request().method(), url: this.sanitizeUrl(response.url()), status: response.status(), failed: true });
    });
    page.on('requestfailed', request => onEvent({ type: 'network', method: request.method(), url: this.sanitizeUrl(request.url()), status: 0, failed: true, error: this.redactSecrets(request.failure()?.errorText || '') }));
  }
  private async captureScreenshot(stepId: string, kind: 'pass' | 'fail'): Promise<string | null> {
    if (!this.page || this.page.isClosed()) return null;
    try {
      const dir = path.join(this.artifactRootDir, 'screenshots');
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      const screenshotPath = uniqueArtifactPath(dir, `${kind}-${safeArtifactFilename(stepId, 'step')}-${Date.now()}.png`, `${kind}-step.png`);
      await this.page.screenshot({ path: screenshotPath, fullPage: true });
      return screenshotPath;
    } catch {
      return null;
    }
  }
  private async cleanup(): Promise<void> {
    try {
      if (this.page && !this.page.isClosed()) {
        await this.page.close().catch(() => {});
      }
      if (this.context) {
        await this.context.close().catch(() => {});
      }
      if (this.browser && this.browser.isConnected()) {
        await this.browser.close().catch(() => {});
      }
    } finally {
      this.page = null;
      this.context = null;
      this.browser = null;
    }
  }
}


















