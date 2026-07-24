/**
 * Playwright worker 鈥?browser lifecycle management.
 *
 * Phase 0 proof: launch/close Chromium without orphan processes.
 * Phase 1+: step execution, screenshots, traces, video.
 *
 * Per Section 4.2:
 *   - Use `playwright`, not Selenium or custom CDP wrappers.
 *   - Pin Playwright and browser revisions in the lockfile.
 *   - Chromium is the only required version 1 browser.
 *   - Use Locator APIs and Playwright auto-waiting.
 *   - Never add unconditional sleeps as the default synchronization strategy.
 */

import { chromium, Browser, BrowserContext, Page } from 'playwright';
import { chromiumLaunchTarget } from './browser-runtime';
import * as path from 'path';
import * as fs from 'fs';

// ------------------------------------------------------------------
// Types
// ------------------------------------------------------------------

export interface LaunchOptions {
  headless: boolean;
  slowMo?: number;
  viewport?: { width: number; height: number } | null;
  locale?: string | null;
  timezoneId?: string | null;
  colorScheme?: 'light' | 'dark' | 'no-preference' | null;
}

export interface BrowserStatus {
  isReady: boolean;
  browserVersion: string | null;
  engineVersion: string;
}

// ------------------------------------------------------------------
// State (singleton within the worker process)
// ------------------------------------------------------------------

let browser: Browser | null = null;
let context: BrowserContext | null = null;
let page: Page | null = null;

// Track whether we initiated the close (to distinguish user close from crash)
let _closing = false;

// ------------------------------------------------------------------
// Public API
// ------------------------------------------------------------------

/**
 * Launch Chromium with the given options.
 * Throws if a browser is already running 鈥?call closeBrowser() first.
 */
export async function launchBrowser(opts: LaunchOptions): Promise<{
  browserVersion: string;
  chromiumPath: string;
}> {
  if (browser && browser.isConnected()) {
    throw new Error('Browser is already running. Call closeBrowser() first.');
  }

  const target = chromiumLaunchTarget();
  let launchedBrowser: Awaited<ReturnType<typeof chromium.launch>> | null = null;
  try {
    launchedBrowser = await chromium.launch({
      headless: opts.headless,
      slowMo: opts.slowMo ?? 0,
      ...('executablePath' in target
        ? { executablePath: target.executablePath }
        : 'channel' in target
          ? { channel: target.channel }
          : {}),
    });
    browser = launchedBrowser;

    context = await browser.newContext({
      viewport: opts.viewport ?? undefined,
      locale: opts.locale ?? undefined,
      timezoneId: opts.timezoneId ?? undefined,
      colorScheme: opts.colorScheme ?? undefined,
    });

    page = await context.newPage();

    // Listen for unexpected disconnect
    browser.on('disconnected', () => {
      if (!_closing) {
        console.warn('[Playwright] Browser disconnected unexpectedly');
      }
      browser = null;
      context = null;
      page = null;
    });

    return {
      browserVersion: browser.version(),
      chromiumPath: 'executablePath' in target ? target.executablePath : 'Google Chrome channel',
    };
  } catch (error) {
    // Partial launch must not leak browser processes.
    try {
      if (page && !page.isClosed()) await page.close().catch(() => {});
    } catch { /* ignore */ }
    try {
      if (context) await context.close().catch(() => {});
    } catch { /* ignore */ }
    try {
      if (launchedBrowser && launchedBrowser.isConnected()) await launchedBrowser.close().catch(() => {});
    } catch { /* ignore */ }
    browser = null;
    context = null;
    page = null;
    throw error;
  }
}

/**
 * Close the browser and clean up all resources.
 * Idempotent 鈥?safe to call multiple times.
 */
export async function closeBrowser(): Promise<void> {
  _closing = true;
  try {
    if (page && !page.isClosed()) {
      await page.close().catch(() => {});
    }
    if (context) {
      await context.close().catch(() => {});
    }
    if (browser && browser.isConnected()) {
      await browser.close().catch(() => {});
    }
  } finally {
    page = null;
    context = null;
    browser = null;
    _closing = false;
  }
}

/**
 * Get the current browser status.
 */
export function getBrowserStatus(): BrowserStatus {
  return {
    isReady: browser !== null && browser.isConnected(),
    browserVersion: browser?.version() ?? null,
    engineVersion: require('playwright/package.json').version,
  };
}

/**
 * Get the current page (for step execution).
 * Throws if browser is not ready.
 */
export function getPage(): Page {
  if (!page || !browser?.isConnected()) {
    throw new Error('Browser is not ready. Call launchBrowser() first.');
  }
  return page;
}

/**
 * Get the current browser context.
 */
export function getContext(): BrowserContext {
  if (!context || !browser?.isConnected()) {
    throw new Error('Browser is not ready. Call launchBrowser() first.');
  }
  return context;
}

/**
 * Ensure all browser processes are killed.
 * Called on app quit to prevent orphan processes.
 */
export async function forceCleanup(): Promise<void> {
  await closeBrowser();
  // Playwright handles process cleanup internally on browser.close().
  // No additional orphan prevention needed if closeBrowser() succeeds.
}

