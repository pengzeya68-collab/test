import * as fs from 'fs';
import * as path from 'path';

export function bundledChromiumExecutable(): string | undefined {
  const resourcesPath = (process as NodeJS.Process & { resourcesPath?: string }).resourcesPath;
  if (!resourcesPath) return undefined;
  const browserRoot = path.join(resourcesPath, 'browsers');
  if (!fs.existsSync(browserRoot)) return undefined;
  const revision = fs.readdirSync(browserRoot).find(name => /^chromium-\d+$/.test(name));
  if (!revision) return undefined;
  const executable = path.join(browserRoot, revision, 'chrome-win', 'chrome.exe');
  return fs.existsSync(executable) ? executable : undefined;
}

