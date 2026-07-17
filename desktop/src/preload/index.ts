/**
 * Preload bridge 閳?the only communication channel between renderer and main.
 */

import { contextBridge, ipcRenderer } from 'electron';
// Sandboxed preload scripts may only require Electron and a small set of Node
// built-ins. Keep the bridge self-contained so it also works from app.asar.
type IpcType =
  | 'browser.launch'
  | 'browser.close'
  | 'browser.status'
  | 'page.goto'
  | 'page.screenshot'
  | 'element.click'
  | 'element.fill'
  | 'artifact.read'
  | 'execution.cancel';

const IPC_TIMEOUTS: Record<IpcType, number> = {
  'browser.launch': 60_000,
  'browser.close': 15_000,
  'browser.status': 5_000,
  'page.goto': 60_000,
  'page.screenshot': 15_000,
  'element.click': 30_000,
  'element.fill': 30_000,
  'artifact.read': 15_000,
  'execution.cancel': 10_000,
};

function newCorrelationId(): string {
  return crypto.randomUUID();
}

async function ipcCall<T extends IpcType>(type: T, payload: unknown): Promise<any> {
  const correlationId = newCorrelationId();
  const channel = `ipc:${type}`;
  const timeoutMs = IPC_TIMEOUTS[type] ?? 30_000;
  const request = { correlationId, type, payload };

  const result = await Promise.race([
    ipcRenderer.invoke(channel, request),
    new Promise<never>((_, reject) => setTimeout(() => reject(new Error('IPC timeout')), timeoutMs)),
  ]);

  if (!result.success) {
    const err = new Error(result.errorMessage || 'IPC call failed');
    (err as any).code = result.errorCode;
    (err as any).correlationId = correlationId;
    throw err;
  }

  return result.data;
}

let recorderEventChannel = '';
let recorderEventListener: ((_event: unknown, data: unknown) => void) | null = null;

function clearRecorderListener(): void {
  if (recorderEventChannel && recorderEventListener) ipcRenderer.removeListener(recorderEventChannel, recorderEventListener);
  recorderEventChannel = '';
  recorderEventListener = null;
}

async function recorderCall(type: 'execution.pause' | 'execution.resume' | 'file.choose' | 'recorder.start' | 'recorder.mode' | 'recorder.validate' | 'recorder.stop' | 'auth-state.validate', payload: unknown): Promise<any> {
  const correlationId = newCorrelationId();
  const result = await ipcRenderer.invoke(`ipc:${type}`, { correlationId, type, payload });
  if (!result?.success) throw new Error(result?.errorMessage || 'Recorder operation failed');
  return result.data;
}
const desktopApi = {
  browser: {
    launch: (opts: {
      headless?: boolean;
      slowMo?: number;
      viewport?: { width: number; height: number } | null;
      locale?: string | null;
      timezoneId?: string | null;
      colorScheme?: 'light' | 'dark' | 'no-preference' | null;
    }) =>
      ipcCall('browser.launch', {
        headless: opts.headless ?? false,
        slowMo: opts.slowMo ?? 0,
        viewport: opts.viewport ?? null,
        locale: opts.locale ?? null,
        timezoneId: opts.timezoneId ?? null,
        colorScheme: opts.colorScheme ?? null,
      }),
    close: () => ipcCall('browser.close', {}),
    status: () => ipcCall('browser.status', {}),
  },

  page: {
    goto: (url: string, opts?: { timeoutMs?: number; waitUntil?: string }) =>
      ipcCall('page.goto', {
        url,
        timeoutMs: opts?.timeoutMs ?? 30000,
        waitUntil: opts?.waitUntil ?? 'load',
      }),
    screenshot: (opts?: { fullPage?: boolean }) =>
      ipcCall('page.screenshot', {
        fullPage: opts?.fullPage ?? false,
      }),
  },

  element: {
    click: (locator: unknown, opts?: { timeoutMs?: number }) =>
      ipcCall('element.click', {
        locator,
        timeoutMs: opts?.timeoutMs ?? 10000,
      }),
    fill: (locator: unknown, value: string, opts?: { timeoutMs?: number }) =>
      ipcCall('element.fill', {
        locator,
        value,
        timeoutMs: opts?.timeoutMs ?? 10000,
      }),
  },

  execution: {
    cancel: (targetCorrelationId: string) => ipcCall('execution.cancel', { targetCorrelationId }),
    pause: (targetCorrelationId: string) => recorderCall('execution.pause' as any, { targetCorrelationId }),
    resume: (targetCorrelationId: string, mode: 'continue' | 'step') => recorderCall('execution.resume' as any, { targetCorrelationId, mode }),
    runCase: (
      caseSnapshot: unknown,
      opts?: {
        environment?: { baseUrl: string; variables: Record<string, string> } | null;
        headless?: boolean;
        screenshotsOnFailure?: boolean;
        traceOnFailure?: boolean;
        debugMode?: boolean;
        authStateId?: string | null;
        runtimeConfigRequest?: { serverUrl: string; token: string; environmentId?: number | null } | null;
        variables?: Record<string, string>;
        onEvent?: (event: unknown) => void;
      }
    ) => {
      const correlationId = newCorrelationId();
      const channel = `ipc:case.run:event:${correlationId}`;

      if (opts?.onEvent) {
        const listener = (_event: unknown, data: unknown) => {
          opts.onEvent?.(data);
        };
        ipcRenderer.on(channel, listener);
      }

      const promise = ipcRenderer.invoke('ipc:case.run', {
        correlationId,
        type: 'case.run',
        payload: {
          caseSnapshot,
          environment: opts?.environment ?? null,
          headless: opts?.headless ?? false,
          screenshotsOnFailure: opts?.screenshotsOnFailure ?? true,
          traceOnFailure: opts?.traceOnFailure ?? true,
          debugMode: opts?.debugMode ?? false,
          authStateId: opts?.authStateId ?? null,
          runtimeConfigRequest: opts?.runtimeConfigRequest ?? null,
          variables: opts?.variables ?? {},
        },
      }).then((result: any) => {
        ipcRenderer.removeAllListeners(channel);
        if (!result.success) {
          throw new Error(result.errorMessage || 'Run failed');
        }
        return result.data;
      });

      return { correlationId, promise };
    },
  },

  authStates: {
    list: () => recorderCall('auth-state.list' as any, {}),
    validate: (id: string, targetUrl: string) => recorderCall('auth-state.validate' as any, { id, targetUrl }),
    saveCurrent: (name: string, id?: string) => recorderCall('auth-state.save' as any, { name, id }),
    delete: (id: string) => recorderCall('auth-state.delete' as any, { id }),
  },

  files: {
    choose: (options?: { multiple?: boolean; filters?: Array<{ name: string; extensions: string[] }> }) =>
      recorderCall('file.choose' as any, { multiple: options?.multiple ?? false, filters: options?.filters ?? [] }),
  },
  recorder: {
    start: async (
      opts: { url: string; viewport?: { width: number; height: number } | null; slowMo?: number; authStateId?: string | null },
      onEvent?: (event: unknown) => void
    ) => {
      clearRecorderListener();
      const correlationId = newCorrelationId();
      recorderEventChannel = `ipc:recorder:event:${correlationId}`;
      recorderEventListener = (_event: unknown, data: unknown) => onEvent?.(data);
      ipcRenderer.on(recorderEventChannel, recorderEventListener);
      const result = await ipcRenderer.invoke('ipc:recorder.start', {
        correlationId,
        type: 'recorder.start',
        payload: { url: opts.url, viewport: opts.viewport ?? null, slowMo: opts.slowMo ?? 0, authStateId: opts.authStateId ?? null },
      });
      if (!result?.success) {
        clearRecorderListener();
        throw new Error(result?.errorMessage || 'Recorder start failed');
      }
      return result.data;
    },
    setMode: (mode: 'record' | 'assert-visible' | 'assert-text') => recorderCall('recorder.mode', { mode }),
    validateLocator: (locator: unknown) => recorderCall('recorder.validate', { locator }),
    stop: async () => {
      try { return await recorderCall('recorder.stop', {}); }
      finally { clearRecorderListener(); }
    },
  },
  artifacts: {
    read: (artifactPath: string) => ipcCall('artifact.read', { path: artifactPath }),
  },

  versions: {
    electron: process.versions.electron,
    node: process.versions.node,
    chromium: process.versions.chrome,
    platform: process.platform,
  },
};

contextBridge.exposeInMainWorld('testmaster', desktopApi);
export type DesktopApi = typeof desktopApi;








