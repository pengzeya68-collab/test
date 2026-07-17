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

import { app, BrowserWindow, Menu } from 'electron';
import { createMainWindow, getMainWindow } from './window';
import { registerIpcHandlers, stopActiveRecorder, unregisterIpcHandlers } from './ipc';
import { forceCleanup } from '../worker/playwright-worker';
import { ensureLocalBackend, stopLocalBackend } from './backend-service';

// Prevent multiple instances
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
}

app.on('second-instance', () => {
  const win = getMainWindow();
  if (win) {
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

// ------------------------------------------------------------------
// App lifecycle
// ------------------------------------------------------------------

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);

  // Register IPC handlers
  registerIpcHandlers();

  // Create the main window
  createMainWindow();
  void ensureLocalBackend();

  // macOS: re-create window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
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
  event.preventDefault();

  // Unregister IPC handlers
  unregisterIpcHandlers();

  // Gracefully close browser with a bounded timeout (5 seconds)
  const GRACEFUL_SHUTDOWN_MS = 5000;
  try {
    await Promise.race([
      Promise.all([forceCleanup(), stopActiveRecorder()]),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Graceful shutdown timeout')), GRACEFUL_SHUTDOWN_MS)
      ),
    ]);
  } catch (e) {
    console.error('[Main] Browser cleanup failed or timed out:', e);
    // Force kill happens automatically when the process exits
  }
  stopLocalBackend();

  // Allow the quit to proceed
  app.exit(0);
});

// Prevent content security policy warnings in dev
app.on('web-contents-created', (_event, contents) => {
  // Block any webview creation 鈥?we don't use webviews
  contents.on('will-attach-webview', (e) => e.preventDefault());
});

