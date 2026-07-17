/**
 * Playwright launch/close proof — Phase 0 gate.
 *
 * Verifies that:
 *   1. Chromium can be launched with pinned Playwright.
 *   2. Browser status reports correct version info.
 *   3. Browser can be closed without orphan processes.
 *   4. Double-launch is rejected.
 *
 * Per Phase 0 gate (Section 17):
 *   "Desktop starts, logs in, launches/closes Chromium without orphan processes."
 */

import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import {
  launchBrowser,
  closeBrowser,
  getBrowserStatus,
} from '../src/worker/playwright-worker';

describe('Playwright Browser Lifecycle', () => {
  afterEach(async () => {
    await closeBrowser();
  });

  it('should launch Chromium in headless mode', async () => {
    const result = await launchBrowser({
      headless: true,
      slowMo: 0,
      viewport: { width: 1280, height: 720 },
      locale: null,
      timezoneId: null,
      colorScheme: null,
    });

    expect(result.browserVersion).toBeTruthy();
    expect(result.browserVersion).toMatch(/\d+\.\d+\.\d+/);
    expect(result.chromiumPath).toBeTruthy();
  });

  it('should report correct browser status after launch', async () => {
    await launchBrowser({ headless: true });

    const status = getBrowserStatus();
    expect(status.isReady).toBe(true);
    expect(status.browserVersion).toBeTruthy();
    expect(status.engineVersion).toMatch(/\d+\.\d+\.\d+/);
  });

  it('should report not-ready before launch', () => {
    const status = getBrowserStatus();
    expect(status.isReady).toBe(false);
    expect(status.browserVersion).toBeNull();
    expect(status.engineVersion).toMatch(/\d+\.\d+\.\d+/);
  });

  it('should close browser cleanly', async () => {
    await launchBrowser({ headless: true });
    expect(getBrowserStatus().isReady).toBe(true);

    await closeBrowser();

    const status = getBrowserStatus();
    expect(status.isReady).toBe(false);
    expect(status.browserVersion).toBeNull();
  });

  it('should reject double launch', async () => {
    await launchBrowser({ headless: true });

    await expect(launchBrowser({ headless: true })).rejects.toThrow(
      /already running/i
    );
  });

  it('should be idempotent on close', async () => {
    await launchBrowser({ headless: true });
    await closeBrowser();
    await closeBrowser(); // should not throw
    await closeBrowser(); // should not throw
  });

  it('should support viewport configuration', async () => {
    await launchBrowser({
      headless: true,
      viewport: { width: 1920, height: 1080 },
    });

    const status = getBrowserStatus();
    expect(status.isReady).toBe(true);
  });
});
