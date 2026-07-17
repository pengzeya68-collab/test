/**
 * Electron main process 鈥?window creation with strict security settings.
 *
 * Per Section 4.1 of the Implementation Spec:
 *   - contextIsolation: true
 *   - nodeIntegration: false
 *   - sandbox: true (compatible with preload bridge)
 *   - Disable navigation to untrusted origins
 *   - Deny unexpected permission requests
 */

import { BrowserWindow, session, shell } from 'electron';
import * as path from 'path';
import { fileURLToPath } from 'url';

const DEV_RENDERER_ORIGINS = new Set(['http://localhost:5173', 'http://127.0.0.1:5173']);
const RENDERER_ROOT = path.resolve(__dirname, '../renderer');

function isAllowedOrigin(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'file:') {
      const candidate = path.resolve(fileURLToPath(parsed));
      return candidate === RENDERER_ROOT || candidate.startsWith(`${RENDERER_ROOT}${path.sep}`);
    }
    return process.env.NODE_ENV !== 'production' && DEV_RENDERER_ORIGINS.has(parsed.origin);
  } catch {
    return false;
  }
}

let mainWindow: BrowserWindow | null = null;

export function getMainWindow(): BrowserWindow | null {
  return mainWindow;
}

export function createMainWindow(): BrowserWindow {
  const isDev = process.env.NODE_ENV !== 'production' && !!process.env.VITE_DEV_SERVER_URL;
  const rendererUrl =
    process.env.VITE_DEV_SERVER_URL ||
    `file://${path.join(__dirname, '../renderer/index.html')}`;

  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'TestMaster Desktop',
    backgroundColor: '#f5f7fa',
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      preload: path.join(__dirname, '../preload/index.js'),
    },
  });

  win.webContents.on('will-navigate', (event, url) => {
    if (!isAllowedOrigin(url)) {
      console.warn(`[Security] Blocked navigation to untrusted origin: ${url}`);
      event.preventDefault();
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
        void shell.openExternal(url);
      }
    } catch {
      // Invalid and non-web URLs are denied without side effects.
    }
    return { action: 'deny' };
  });

  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => {
    callback(false);
  });

  win.once('ready-to-show', () => {
    win.show();
  });

  win.on('closed', () => {
    mainWindow = null;
  });

  if (isDev) {
    void win.loadURL(rendererUrl);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    void win.loadURL(rendererUrl);
  }

  mainWindow = win;
  return win;
}

export function getSecurityConfig() {
  return {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    webSecurity: true,
    allowRunningInsecureContent: false,
  };
}

export function _testIsAllowedOrigin(url: string): boolean {
  return isAllowedOrigin(url);
}
