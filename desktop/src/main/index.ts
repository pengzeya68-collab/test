/**
 * Electron main process entry point.
 *
 * Per Section 4.1 of the Implementation Spec:
 *   - Use a currently supported stable Electron version, pinned exactly.
 *   - contextIsolation: true, nodeIntegration: false, sandbox: true.
 *   - Disable navigation to untrusted origins.
 *   - Deny unexpected permission requests.
 *
 * Per Section 9.4 (Cancellation):
 *   - The worker closes page/context/browser and marks unfinished steps cancelled.
 *   - Force-kill is permitted after a bounded graceful shutdown period.
 */

import { app, BrowserWindow, Menu, nativeImage, NativeImage, Tray } from 'electron';
import { createMainWindow, getMainWindow } from './window';
import {
  initializeDesktopAgent,
  isDesktopAgentEnabled,
  registerIpcHandlers,
  stopActiveRecorder,
  stopDesktopAgent,
  unregisterIpcHandlers,
} from './ipc';
import { forceCleanup } from '../worker/playwright-worker';
import { ensureLocalBackend, stopLocalBackend } from './backend-service';
import { configureDesktopDataDirectory } from './desktop-data-directory';

// This must happen before app.whenReady so every Electron-owned file follows
// the configured/non-system data root.
configureDesktopDataDirectory();

// Prevent multiple instances
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
}

app.on('second-instance', () => {
  const win = getMainWindow();
  if (win) {
    if (!win.isVisible()) win.show();
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

let tray: Tray | null = null;
let forceQuitRequested = false;
let shutdownStarted = false;

function createTrayIcon(): NativeImage {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" rx="6" fill="#2563eb"/><text x="16" y="21" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" font-weight="700" fill="white">TM</text></svg>';
  const svgIcon = nativeImage
    .createFromDataURL(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`)
    .resize({ width: 16, height: 16 });
  if (!svgIcon.isEmpty()) return svgIcon;

  // Windows cannot use an executable as a Tray image. Some Electron builds do
  // not decode SVG data URLs, so create a small BGRA bitmap that is guaranteed
  // to be valid instead of falling back to process.execPath.
  const size = 16;
  const pixels = Buffer.alloc(size * size * 4);
  for (let y = 1; y < size - 1; y += 1) {
    for (let x = 1; x < size - 1; x += 1) {
      const offset = (y * size + x) * 4;
      pixels[offset] = 235; // B
      pixels[offset + 1] = 99; // G
      pixels[offset + 2] = 37; // R
      pixels[offset + 3] = 255; // A
    }
  }
  return nativeImage.createFromBitmap(pixels, { width: size, height: size, scaleFactor: 1 });
}

function createManagedMainWindow(): BrowserWindow {
  const win = createMainWindow();
  win.on('close', (event) => {
    if (!forceQuitRequested && isDesktopAgentEnabled()) {
      event.preventDefault();
      win.hide();
    }
  });
  return win;
}

function createTray(): void {
  if (tray) return;
  const icon = createTrayIcon();
  if (icon.isEmpty()) {
    console.error('[Main] Unable to create the TestMaster tray icon.');
    return;
  }
  try {
    tray = new Tray(icon);
  } catch (error) {
    console.error('[Main] Unable to create the TestMaster tray:', error);
    return;
  }
  tray.setToolTip('TestMaster Desktop');
  tray.setContextMenu(Menu.buildFromTemplate([
    {
      label: '打开 TestMaster',
      click: () => {
        const win = getMainWindow() ?? createManagedMainWindow();
        win.show();
        if (win.isMinimized()) win.restore();
        win.focus();
      },
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        forceQuitRequested = true;
        app.quit();
      },
    },
  ]));
  tray.on('click', () => {
    const win = getMainWindow() ?? createManagedMainWindow();
    win.show();
    if (win.isMinimized()) win.restore();
    win.focus();
  });
}

// ------------------------------------------------------------------
// App lifecycle
// ------------------------------------------------------------------

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);

  // Register IPC handlers
  registerIpcHandlers();

  // Create the main window
  createManagedMainWindow();
  createTray();
  void ensureLocalBackend()
    .catch((error) => {
      console.error('[Main] Local backend startup failed:', error);
      return { ready: false, managed: false, error: String(error) };
    })
    .finally(() => {
      try {
        initializeDesktopAgent();
      } catch (error) {
        console.error('[Main] Desktop agent init failed:', error);
      }
    });

  // macOS: re-create window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createManagedMainWindow();
    }
  });
});

// ------------------------------------------------------------------
// Quit behavior
// ------------------------------------------------------------------

app.on('window-all-closed', () => {
  // On macOS, apps typically stay active until explicitly quit
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// ------------------------------------------------------------------
// Cleanup 鈥?prevent orphan browser/worker processes
// ------------------------------------------------------------------

app.on('before-quit', async (event) => {
  if (shutdownStarted) return;
  event.preventDefault();
  shutdownStarted = true;
  forceQuitRequested = true;

  // Unregister IPC handlers
  unregisterIpcHandlers();

  // Parallel workers may need ~20s to finish run:finish; keep headroom.
  const GRACEFUL_SHUTDOWN_MS = 25_000;
  try {
    await Promise.race([
      Promise.all([
        forceCleanup().catch((e) => console.error('[Main] forceCleanup failed:', e)),
        stopActiveRecorder().catch((e) => console.error('[Main] stopActiveRecorder failed:', e)),
        stopDesktopAgent().catch((e) => console.error('[Main] stopDesktopAgent failed:', e)),
      ]),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Graceful shutdown timeout')), GRACEFUL_SHUTDOWN_MS)
      ),
    ]);
  } catch (e) {
    console.error('[Main] Browser cleanup failed or timed out:', e);
  }

  try {
    stopLocalBackend();
  } catch (e) {
    console.error('[Main] stopLocalBackend failed:', e);
  }
  try {
    tray?.destroy();
  } catch (e) {
    console.error('[Main] tray destroy failed:', e);
  }
  tray = null;

  app.exit(0);
});

// Prevent content security policy warnings in dev
app.on('web-contents-created', (_event, contents) => {
  // Block any webview creation 鈥?we don't use webviews
  contents.on('will-attach-webview', (e) => e.preventDefault());
});

