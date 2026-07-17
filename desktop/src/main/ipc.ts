/**
 * IPC handler registration 閳?bridges renderer requests to the worker.
 *
 * Per Section 3.1 ownership boundaries:
 *   - The renderer sends typed IPC messages via the preload bridge.
 *   - The main process validates them and delegates to the worker.
 *   - The renderer never touches Playwright objects directly.
 */

import { app, BrowserWindow, dialog, ipcMain, IpcMainInvokeEvent, shell } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import {
  IPC_SCHEMAS,
  IpcType,
  IpcErrorCode,
  createSuccessResponse,
  createErrorResponse,
  validateRequest,
} from '../shared/contracts/ipc';
import {
  launchBrowser,
  closeBrowser,
  getBrowserStatus,
  getPage,
} from '../worker/playwright-worker';
import { CaseExecutionEngine, CaseSnapshot, EnvironmentConfig, RunOptions, StepEvent } from '../worker/execution-engine';
import { Locator } from '../shared/contracts/locator';
import { RecorderMode, RecorderSession } from '../worker/recorder-session';
import { getMainWindow } from './window';
import { deleteAuthState, listAuthStates, loadAuthState, saveAuthState } from './auth-state-store';
import { chromium } from 'playwright';
import { bundledChromiumExecutable } from '../worker/browser-runtime';

const activeOperations = new Map<string, AbortController>();
const activeEngines = new Map<string, CaseExecutionEngine>();
let activeRecorder: RecorderSession | null = null;

const artifactRootDir = path.join(app.getPath('userData'), 'artifacts');
const screenshotOutputDir = path.join(artifactRootDir, 'screenshots');

type BrowserLaunchPayload = {
  headless: boolean;
  slowMo: number;
  viewport: { width: number; height: number } | null;
  locale: string | null;
  timezoneId: string | null;
  colorScheme: 'light' | 'dark' | 'no-preference' | null;
};

type GotoPayload = {
  url: string;
  timeoutMs: number;
  waitUntil: 'load' | 'domcontentloaded' | 'networkidle';
};

type ClickPayload = {
  locator: Locator;
  timeoutMs: number;
};

type FillPayload = {
  locator: Locator;
  value: string;
  timeoutMs: number;
};

type ScreenshotPayload = {
  fullPage: boolean;
};

type ArtifactReadPayload = {
  path: string;
};

type RunCasePayload = {
  caseSnapshot: CaseSnapshot;
  environment: EnvironmentConfig | null;
  headless: boolean;
  screenshotsOnFailure: boolean;
  traceOnFailure: boolean;
  debugMode: boolean;
  authStateId?: string | null;
  runtimeConfigRequest?: { serverUrl: string; token: string; environmentId?: number | null } | null;
  variables?: Record<string, string>;
};

type CancelPayload = {
  targetCorrelationId: string;
};

function assertTrustedSender(event: IpcMainInvokeEvent): BrowserWindow {
  const senderWindow = BrowserWindow.fromWebContents(event.sender);
  const mainWindow = getMainWindow();

  if (!senderWindow || !mainWindow || senderWindow !== mainWindow || event.sender.isDestroyed()) {
    throw new Error('UNTRUSTED_IPC_SENDER');
  }

  return senderWindow;
}

function resolveArtifactPath(candidatePath: string): string {
  const resolvedPath = path.resolve(candidatePath);
  const allowedRoots = [artifactRootDir, app.getPath('temp')].map((dir) => path.resolve(dir));
  const isAllowed = allowedRoots.some((rootDir) => resolvedPath === rootDir || resolvedPath.startsWith(`${rootDir}${path.sep}`));
  if (!isAllowed) {
    throw new Error('ARTIFACT_PATH_NOT_ALLOWED');
  }
  return resolvedPath;
}

async function handleBrowserLaunch(
  payload: BrowserLaunchPayload
): Promise<{ browserVersion: string; chromiumPath: string }> {
  return launchBrowser({
    headless: payload.headless,
    slowMo: payload.slowMo,
    viewport: payload.viewport,
    locale: payload.locale,
    timezoneId: payload.timezoneId,
    colorScheme: payload.colorScheme,
  });
}

async function handleBrowserClose(): Promise<null> {
  await closeBrowser();
  return null;
}

async function handleBrowserStatus(): Promise<{
  isReady: boolean;
  browserVersion: string | null;
  engineVersion: string;
}> {
  return getBrowserStatus();
}

async function handleGoto(
  payload: GotoPayload
): Promise<{ finalUrl: string; title: string }> {
  const page = getPage();
  await page.goto(payload.url, {
    timeout: payload.timeoutMs,
    waitUntil: payload.waitUntil,
  });
  return {
    finalUrl: page.url(),
    title: await page.title(),
  };
}

async function handleClick(
  payload: ClickPayload
): Promise<null> {
  const page = getPage();
  const locator = resolveLocator(page, payload.locator);
  await locator.click({ timeout: payload.timeoutMs });
  return null;
}

async function handleFill(
  payload: FillPayload
): Promise<null> {
  const page = getPage();
  const locator = resolveLocator(page, payload.locator);
  await locator.fill(payload.value, { timeout: payload.timeoutMs });
  return null;
}

async function handleScreenshot(
  payload: ScreenshotPayload
): Promise<{ path: string }> {
  const page = getPage();
  fs.mkdirSync(screenshotOutputDir, { recursive: true });
  const filepath = path.join(screenshotOutputDir, `screenshot-${Date.now()}.png`);
  await page.screenshot({ path: filepath, fullPage: payload.fullPage });
  return { path: filepath };
}

async function handleReadArtifact(payload: ArtifactReadPayload): Promise<{ filename: string; sizeBytes: number; contentBase64: string }> {
  const resolvedPath = resolveArtifactPath(payload.path);
  const buffer = await fs.promises.readFile(resolvedPath);
  return {
    filename: path.basename(resolvedPath),
    sizeBytes: buffer.byteLength,
    contentBase64: buffer.toString('base64'),
  };
}

function resolveLocator(page: import('playwright').Page, loc: Locator): import('playwright').Locator {
  let scope: import('playwright').Page | import('playwright').FrameLocator = page;
  for (const selector of loc.framePath ?? []) {
    scope = scope.frameLocator(selector);
  }

  switch (loc.strategy) {
    case 'test_id':
      return scope.getByTestId(loc.value);
    case 'role':
      return scope.getByRole(loc.value as never, loc.options as never);
    case 'label':
      return scope.getByLabel(loc.value, loc.options as never);
    case 'placeholder':
      return scope.getByPlaceholder(loc.value, loc.options as never);
    case 'text':
      return scope.getByText(loc.value, loc.options as never);
    case 'css':
      return scope.locator(loc.value);
    case 'xpath':
      return scope.locator(`xpath=${loc.value}`);
    default:
      throw new Error(`Unknown locator strategy: ${loc.strategy}`);
  }
}

async function loadRuntimeEnvironment(request: RunCasePayload['runtimeConfigRequest']): Promise<EnvironmentConfig | null> {
  if (!request) return null;
  const serverUrl = request.serverUrl.replace(/\/$/, '');
  if (!/^https?:\/\//i.test(serverUrl)) throw new Error('INVALID_SERVER_URL');
  const query = request.environmentId != null ? '?environment_id=' + encodeURIComponent(String(request.environmentId)) : '';
  const response = await fetch(serverUrl + '/api/ui-automation/runtime-config' + query, {
    headers: { Authorization: 'Bearer ' + request.token },
  });
  if (!response.ok) throw new Error('RUNTIME_CONFIG_FAILED_' + response.status);
  const data: any = await response.json();
  return { baseUrl: data.base_url || '', variables: data.variables || {}, secretKeys: data.secret_keys || [] };
}
async function validateAuthState(id: string, targetUrl: string): Promise<Record<string, unknown>> {
  if (!/^https?:\/\//i.test(targetUrl || '')) return { valid: true, status: 'not-applicable', reason: '当前用例没有可验证的 HTTP 页面' };
  const storageState: any = loadAuthState(id);
  const cookies = Array.isArray(storageState?.cookies) ? storageState.cookies : [];
  const nowSeconds = Date.now() / 1000;
  const persistent = cookies.filter((cookie: any) => Number(cookie.expires) > 0);
  if (cookies.length > 0 && persistent.length === cookies.length && persistent.every((cookie: any) => Number(cookie.expires) <= nowSeconds)) {
    return { valid: false, status: 'expired', reason: '登录 Cookie 已全部过期', targetUrl };
  }
  const browser = await chromium.launch({ headless: true, executablePath: bundledChromiumExecutable() });
  try {
    const context = await browser.newContext({ storageState });
    const page = await context.newPage();
    const response = await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    await page.waitForTimeout(500);
    const finalUrl = page.url();
    const title = await page.title().catch(() => '');
    const visiblePasswords = await page.locator('input[type="password"]:visible').count().catch(() => 0);
    const loginLikeUrl = /(?:^|[\/_-])(login|signin|sign-in|auth|captcha)(?:[\/_?=&-]|$)/i.test(finalUrl);
    const serverError = (response?.status() || 0) >= 500;
    const valid = !visiblePasswords && !loginLikeUrl && !serverError;
    await context.close();
    return { valid, status: valid ? 'valid' : 'invalid', reason: serverError ? '目标系统服务异常' : visiblePasswords ? '页面要求重新输入密码或验证码' : loginLikeUrl ? '访问后被带回登录或验证页面' : '登录态可用', targetUrl, finalUrl, title, cookieCount: cookies.length };
  } finally {
    await browser.close().catch(() => {});
  }
}
async function handleRunCase(
  senderWindow: BrowserWindow,
  correlationId: string,
  payload: RunCasePayload
): Promise<unknown> {
  const engine = new CaseExecutionEngine();
  activeEngines.set(correlationId, engine);

  const runtimeEnvironment = await loadRuntimeEnvironment(payload.runtimeConfigRequest);
  const options: RunOptions = {
    headless: payload.headless,
    screenshotsOnFailure: payload.screenshotsOnFailure,
    traceOnFailure: payload.traceOnFailure,
    debugMode: payload.debugMode,
    storageState: payload.authStateId ? loadAuthState(payload.authStateId) : null,
  };

  const onEvent = (event: StepEvent) => {
    if (!senderWindow.isDestroyed()) {
      senderWindow.webContents.send(`ipc:case.run:event:${correlationId}`, event);
    }
  };

  try {
    const baseEnvironment = runtimeEnvironment || payload.environment;
    const executionEnvironment = payload.variables ? {
      baseUrl: baseEnvironment?.baseUrl || '', variables: { ...(baseEnvironment?.variables || {}), ...payload.variables },
      secretKeys: baseEnvironment?.secretKeys || [],
    } : baseEnvironment;
    return await engine.execute(payload.caseSnapshot, executionEnvironment, options, onEvent);
  } finally {
    activeEngines.delete(correlationId);
  }
}

export async function stopActiveRecorder(): Promise<void> {
  if (activeRecorder) {
    await activeRecorder.stop().catch(() => {});
    activeRecorder = null;
  }
}
export function registerIpcHandlers(): void {
  const handlerMap: Record<string, (payload: unknown) => Promise<unknown>> = {
    'browser.launch': (payload) => handleBrowserLaunch(payload as BrowserLaunchPayload),
    'browser.close': () => handleBrowserClose(),
    'browser.status': () => handleBrowserStatus(),
    'page.goto': (payload) => handleGoto(payload as GotoPayload),
    'element.click': (payload) => handleClick(payload as ClickPayload),
    'element.fill': (payload) => handleFill(payload as FillPayload),
    'page.screenshot': (payload) => handleScreenshot(payload as ScreenshotPayload),
    'artifact.read': (payload) => handleReadArtifact(payload as ArtifactReadPayload),
  };

  for (const [type, handler] of Object.entries(handlerMap)) {
    const ipcChannel = `ipc:${type}`;

    ipcMain.handle(ipcChannel, async (event, raw: unknown) => {
      let correlationId = 'unknown';
      try {
        assertTrustedSender(event);
        const validated = validateRequest(type as IpcType, raw);
        correlationId = validated.correlationId;

        const controller = new AbortController();
        activeOperations.set(correlationId, controller);

        const timeoutMs = IPC_SCHEMAS[type as IpcType]?.timeoutMs ?? 30000;
        const result = await Promise.race([
          handler(validated.payload),
          new Promise<never>((_, reject) => setTimeout(() => reject(new Error('TIMEOUT')), timeoutMs)),
        ]);

        activeOperations.delete(correlationId);
        return createSuccessResponse(correlationId, type, result);
      } catch (error: any) {
        activeOperations.delete(correlationId);

        const errorCode: IpcErrorCode = error?.message === 'TIMEOUT'
          ? 'TIMEOUT'
          : error?.message === 'UNTRUSTED_IPC_SENDER' || error?.message === 'ARTIFACT_PATH_NOT_ALLOWED'
            ? 'PERMISSION_DENIED'
            : error?.code === 'VALIDATION_ERROR'
              ? 'VALIDATION_ERROR'
              : 'INTERNAL_ERROR';

        return createErrorResponse(correlationId, type, errorCode, error?.message ?? String(error));
      }
    });
  }

  ipcMain.handle('ipc:case.run', async (event, raw: unknown) => {
    let correlationId = 'unknown';
    try {
      const senderWindow = assertTrustedSender(event);
      const validated = validateRequest('case.run', raw);
      correlationId = validated.correlationId;
      const payload = validated.payload as RunCasePayload;
      const result = await handleRunCase(senderWindow, correlationId, payload);
      return createSuccessResponse(correlationId, 'case.run', result);
    } catch (error: any) {
      const errorCode: IpcErrorCode = error?.message === 'UNTRUSTED_IPC_SENDER' ? 'PERMISSION_DENIED' : 'EXECUTION_ERROR';
      return createErrorResponse(correlationId, 'case.run', errorCode, error?.message ?? String(error));
    }
  });



  ipcMain.handle('ipc:file.choose', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      const owner = assertTrustedSender(event);
      const payload = raw?.payload || {};
      const result = await dialog.showOpenDialog(owner, {
        title: '选择测试文件',
        properties: payload.multiple ? ['openFile', 'multiSelections'] : ['openFile'],
        filters: Array.isArray(payload.filters) ? payload.filters : [],
      });
      return createSuccessResponse(correlationId, 'file.choose', { cancelled: result.canceled, paths: result.filePaths });
    } catch (error: any) {
      return createErrorResponse(correlationId, 'file.choose', 'INTERNAL_ERROR', error?.message ?? String(error));
    }
  });
  ipcMain.handle('ipc:recorder.start', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      const senderWindow = assertTrustedSender(event);
      const payload = raw?.payload || {};
      if (typeof payload.url !== 'string' || payload.url.length > 4096) throw new Error('INVALID_RECORDER_URL');
      await stopActiveRecorder();
      activeRecorder = new RecorderSession((recorderEvent) => {
        if (!senderWindow.isDestroyed()) senderWindow.webContents.send(`ipc:recorder:event:${correlationId}`, recorderEvent);
      });
      const result = await activeRecorder.start({
        url: payload.url,
        viewport: payload.viewport ?? null,
        slowMo: payload.slowMo ?? 0,
        storageState: payload.authStateId ? loadAuthState(payload.authStateId) : null,
      });
      return createSuccessResponse(correlationId, 'recorder.start', result);
    } catch (error: any) {
      await stopActiveRecorder();
      return createErrorResponse(correlationId, 'recorder.start', 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });

  ipcMain.handle('ipc:recorder.mode', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      if (!activeRecorder) throw new Error('RECORDER_NOT_RUNNING');
      const mode = raw?.payload?.mode as RecorderMode;
      if (!['record', 'assert-visible', 'assert-text'].includes(mode)) throw new Error('INVALID_RECORDER_MODE');
      await activeRecorder.setMode(mode);
      return createSuccessResponse(correlationId, 'recorder.mode', { mode });
    } catch (error: any) {
      return createErrorResponse(correlationId, 'recorder.mode', 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });


  ipcMain.handle('ipc:recorder.validate', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      if (!activeRecorder) throw new Error('RECORDER_NOT_RUNNING');
      const locator = raw?.payload?.locator as Locator;
      if (!locator?.strategy || typeof locator.value !== 'string') throw new Error('INVALID_LOCATOR');
      const result = await activeRecorder.validateLocator(locator);
      return createSuccessResponse(correlationId, 'recorder.validate', result);
    } catch (error: any) {
      return createErrorResponse(correlationId, 'recorder.validate', 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });
  ipcMain.handle('ipc:auth-state.list', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try { assertTrustedSender(event); return createSuccessResponse(correlationId, 'auth-state.list' as any, listAuthStates()); }
    catch (error: any) { return createErrorResponse(correlationId, 'auth-state.list' as any, 'EXECUTION_ERROR', error?.message ?? String(error)); }
  });

  ipcMain.handle('ipc:auth-state.validate', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      const result = await validateAuthState(String(raw?.payload?.id || ''), String(raw?.payload?.targetUrl || ''));
      return createSuccessResponse(correlationId, 'auth-state.validate' as any, result);
    } catch (error: any) {
      return createErrorResponse(correlationId, 'auth-state.validate' as any, 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });
  ipcMain.handle('ipc:auth-state.save', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      if (!activeRecorder) throw new Error('RECORDER_NOT_RUNNING');
      const state = await activeRecorder.getStorageState();
      return createSuccessResponse(correlationId, 'auth-state.save' as any, saveAuthState(raw?.payload?.name || '', state, raw?.payload?.id));
    } catch (error: any) { return createErrorResponse(correlationId, 'auth-state.save' as any, 'EXECUTION_ERROR', error?.message ?? String(error)); }
  });

  ipcMain.handle('ipc:auth-state.delete', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try { assertTrustedSender(event); deleteAuthState(raw?.payload?.id); return createSuccessResponse(correlationId, 'auth-state.delete' as any, null); }
    catch (error: any) { return createErrorResponse(correlationId, 'auth-state.delete' as any, 'EXECUTION_ERROR', error?.message ?? String(error)); }
  });
  ipcMain.handle('ipc:recorder.stop', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      await stopActiveRecorder();
      return createSuccessResponse(correlationId, 'recorder.stop', null);
    } catch (error: any) {
      return createErrorResponse(correlationId, 'recorder.stop', 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });

  ipcMain.handle('ipc:execution.pause', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      const engine = activeEngines.get(raw?.payload?.targetCorrelationId);
      if (!engine) throw new Error('EXECUTION_NOT_RUNNING');
      engine.pause();
      return createSuccessResponse(correlationId, 'execution.pause', null);
    } catch (error: any) {
      return createErrorResponse(correlationId, 'execution.pause', 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });

  ipcMain.handle('ipc:execution.resume', async (event, raw: any) => {
    const correlationId = raw?.correlationId || 'unknown';
    try {
      assertTrustedSender(event);
      const engine = activeEngines.get(raw?.payload?.targetCorrelationId);
      if (!engine) throw new Error('EXECUTION_NOT_RUNNING');
      const mode = raw?.payload?.mode === 'step' ? 'step' : 'continue';
      engine.resume(mode);
      return createSuccessResponse(correlationId, 'execution.resume', { mode });
    } catch (error: any) {
      return createErrorResponse(correlationId, 'execution.resume', 'EXECUTION_ERROR', error?.message ?? String(error));
    }
  });
  ipcMain.handle('ipc:execution.cancel', async (event, raw: unknown) => {
    try {
      assertTrustedSender(event);
      const validated = validateRequest('execution.cancel', raw);
      const payload = validated.payload as CancelPayload;
      const targetId = payload.targetCorrelationId;

      const engine = activeEngines.get(targetId);
      if (engine) {
        await engine.cancel();
      }

      const controller = activeOperations.get(targetId);
      if (controller) {
        controller.abort();
        activeOperations.delete(targetId);
      }

      return createSuccessResponse(validated.correlationId, 'execution.cancel', null);
    } catch (error: any) {
      const errorCode: IpcErrorCode = error?.message === 'UNTRUSTED_IPC_SENDER' ? 'PERMISSION_DENIED' : 'INTERNAL_ERROR';
      return createErrorResponse('unknown', 'execution.cancel', errorCode, error?.message ?? String(error));
    }
  });
}

export function unregisterIpcHandlers(): void {
  const channels = [
    'ipc:browser.launch',
    'ipc:browser.close',
    'ipc:browser.status',
    'ipc:page.goto',
    'ipc:element.click',
    'ipc:element.fill',
    'ipc:page.screenshot',
    'ipc:artifact.read',
    'ipc:case.run',
    'ipc:execution.pause',
    'ipc:execution.resume',
    'ipc:execution.cancel',
    'ipc:file.choose',
    'ipc:recorder.start',
    'ipc:recorder.mode',
    'ipc:recorder.validate',
    'ipc:recorder.stop',
    'ipc:auth-state.list',
    'ipc:auth-state.validate',
    'ipc:auth-state.save',
    'ipc:auth-state.delete',
  ];
  for (const ch of channels) {
    if (ipcMain.listenerCount(ch) > 0) {
      ipcMain.removeHandler(ch);
    }
  }
}









