import * as fs from 'fs';
import * as path from 'path';
import { chromium, firefox, webkit, type BrowserType } from 'playwright';

export type BrowserEngine = 'chromium' | 'firefox' | 'webkit';

export type BrowserLaunchTarget =
  | { executablePath: string; source: 'bundled' | 'playwright-cache' }
  | { channel: 'chrome'; source: 'system-chrome' }
  | { source: 'playwright-default' };

function existingFile(candidate: string): string | undefined {
  return fs.existsSync(candidate) ? candidate : undefined;
}

function browserRootCandidates(): string[] {
  const roots: string[] = [];
  const resourcesPath = (process as NodeJS.Process & { resourcesPath?: string }).resourcesPath;
  if (resourcesPath) roots.push(path.join(resourcesPath, 'browsers'));
  if (process.env.LOCALAPPDATA) roots.push(path.join(process.env.LOCALAPPDATA, 'ms-playwright'));
  return roots;
}

function findRevisionExecutable(prefix: string, relativeExe: string): string | undefined {
  for (const root of browserRootCandidates()) {
    if (!fs.existsSync(root)) continue;
    const revision = fs.readdirSync(root).find(name => name.startsWith(prefix));
    if (!revision) continue;
    const candidate = existingFile(path.join(root, revision, relativeExe));
    if (candidate) return candidate;
  }
  return undefined;
}

function bundledChromiumExecutable(): string | undefined {
  return findRevisionExecutable('chromium-', path.join('chrome-win', 'chrome.exe'));
}

function cachedPlaywrightChromiumExecutable(): string | undefined {
  return findRevisionExecutable('chromium-', path.join('chrome-win', 'chrome.exe'));
}

/**
 * Prefer the pinned Chromium delivered with the desktop installer. During
 * development the installer resources are absent, so use a cached Playwright
 * browser or the locally installed Chrome channel.
 */
export function chromiumLaunchTarget(): BrowserLaunchTarget {
  const bundled = bundledChromiumExecutable();
  if (bundled) return { executablePath: bundled, source: 'bundled' };

  const cached = cachedPlaywrightChromiumExecutable();
  if (cached) return { executablePath: cached, source: 'playwright-cache' };

  const systemChrome = [
    process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES, 'Google', 'Chrome', 'Application', 'chrome.exe'),
    process.env['PROGRAMFILES(X86)'] && path.join(process.env['PROGRAMFILES(X86)'], 'Google', 'Chrome', 'Application', 'chrome.exe'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Google', 'Chrome', 'Application', 'chrome.exe'),
  ].filter((candidate): candidate is string => Boolean(candidate)).find(existingFile);
  if (systemChrome) return { channel: 'chrome', source: 'system-chrome' };

  throw new Error('BROWSER_RUNTIME_UNAVAILABLE: 未找到 TestMaster 内置 Chromium。请重新安装桌面端，或在开发环境安装 Google Chrome / 执行 npx playwright install chromium。');
}

export function browserTypeForEngine(engine: BrowserEngine = 'chromium'): BrowserType {
  if (engine === 'firefox') return firefox;
  if (engine === 'webkit') return webkit;
  return chromium;
}

function findFirefoxExecutable(): string | undefined {
  return findRevisionExecutable('firefox-', path.join('firefox', 'firefox.exe'))
    || findRevisionExecutable('firefox-', path.join('firefox', 'Firefox.app', 'Contents', 'MacOS', 'firefox'));
}

function findWebkitExecutable(): string | undefined {
  // Playwright caches webkit under different revision folder names across platforms.
  return findRevisionExecutable('webkit-', path.join('pw_run.sh'))
    || findRevisionExecutable('webkit-', path.join('Playwright.exe'))
    || findRevisionExecutable('webkit-', path.join('minibrowser-wpe', 'MiniBrowser'))
    || findRevisionExecutable('webkit-', path.join('minibrowser-gtk', 'MiniBrowser'));
}

export function isBrowserEngineAvailable(engine: BrowserEngine = 'chromium'): boolean {
  try {
    if (engine === 'chromium') {
      chromiumLaunchTarget();
      return true;
    }
    if (engine === 'firefox') {
      return Boolean(findFirefoxExecutable());
    }
    if (engine === 'webkit') {
      return Boolean(findWebkitExecutable());
    }
  } catch {
    return false;
  }
  return false;
}

export function launchOptionsForEngine(engine: BrowserEngine = 'chromium', headless = true): Record<string, unknown> {
  if (engine === 'chromium') {
    const target = chromiumLaunchTarget();
    if ('executablePath' in target) return { headless, executablePath: target.executablePath };
    if ('channel' in target) return { headless, channel: target.channel };
  }
  if (engine === 'firefox') {
    const exe = findFirefoxExecutable();
    if (!exe) {
      throw new Error('BROWSER_RUNTIME_UNAVAILABLE: Firefox 未安装。请执行 npx playwright install firefox。');
    }
    return { headless, executablePath: exe };
  }
  if (engine === 'webkit') {
    const exe = findWebkitExecutable();
    if (!exe) {
      throw new Error('BROWSER_RUNTIME_UNAVAILABLE: WebKit 未安装。请执行 npx playwright install webkit。');
    }
    return { headless, executablePath: exe };
  }
  return { headless };
}

/** @deprecated use chromiumLaunchTarget / launchOptionsForEngine */
export type ChromiumLaunchTarget = BrowserLaunchTarget;
