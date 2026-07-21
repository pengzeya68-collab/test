import { app } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import { randomUUID } from 'crypto';

export interface DesktopDataDirectoryStatus {
  path: string;
  source: 'configured' | 'non-system-drive' | 'system-fallback';
  isSystemDrive: boolean;
  warning: string | null;
}

interface DirectorySelectionOptions {
  configuredPath?: string;
  systemUserData: string;
  platform?: NodeJS.Platform;
  systemDrive?: string;
  driveRoots?: string[];
  driveExists?: (driveRoot: string) => boolean;
  ensureWritable?: (candidate: string) => boolean;
}

let currentStatus: DesktopDataDirectoryStatus | null = null;

function normalizeDrive(value: string): string {
  return String(value || 'C:').replace(/[\\/]+$/, '').toUpperCase();
}

function defaultDriveRoots(systemDrive: string): string[] {
  const excluded = normalizeDrive(systemDrive);
  return [...'DEFGHIJKLMNOPQRSTUVWXYZAB']
    .map(letter => `${letter}:\\`)
    .filter(root => normalizeDrive(root) !== excluded);
}

function writableDirectory(candidate: string): boolean {
  try {
    fs.mkdirSync(candidate, { recursive: true });
    const probe = path.join(candidate, `.write-test-${process.pid}-${randomUUID()}`);
    fs.writeFileSync(probe, '', { flag: 'wx', mode: 0o600 });
    fs.unlinkSync(probe);
    return true;
  } catch {
    return false;
  }
}

function pathUsesDrive(candidate: string, drive: string): boolean {
  return normalizeDrive(path.parse(path.resolve(candidate)).root) === normalizeDrive(drive);
}

export function selectDesktopDataDirectory(options: DirectorySelectionOptions): DesktopDataDirectoryStatus {
  const platform = options.platform ?? process.platform;
  const systemDrive = normalizeDrive(options.systemDrive || process.env.SystemDrive || path.parse(options.systemUserData).root);
  const ensureWritable = options.ensureWritable ?? writableDirectory;
  const driveExists = options.driveExists ?? fs.existsSync;
  let configurationFailed = false;

  if (options.configuredPath) {
    const configured = path.resolve(options.configuredPath);
    if (path.isAbsolute(options.configuredPath) && ensureWritable(configured)) {
      return {
        path: configured,
        source: 'configured',
        isSystemDrive: platform === 'win32' && pathUsesDrive(configured, systemDrive),
        warning: platform === 'win32' && pathUsesDrive(configured, systemDrive) ? '当前配置的数据目录位于系统盘' : null,
      };
    }
    configurationFailed = true;
  }

  if (platform === 'win32') {
    for (const driveRoot of options.driveRoots ?? defaultDriveRoots(systemDrive)) {
      if (normalizeDrive(driveRoot) === systemDrive || !driveExists(driveRoot)) continue;
      const candidate = path.join(driveRoot, 'TestMasterData');
      if (ensureWritable(candidate)) {
        return {
          path: path.resolve(candidate),
          source: 'non-system-drive',
          isSystemDrive: false,
          warning: configurationFailed ? 'TESTMASTER_DESKTOP_DATA_DIR 不可用，已改用非系统盘数据目录' : null,
        };
      }
    }
  }

  const fallback = path.resolve(options.systemUserData);
  ensureWritable(fallback);
  return {
    path: fallback,
    source: 'system-fallback',
    isSystemDrive: platform === 'win32',
    warning: configurationFailed
      ? '配置目录和非系统盘均不可用，数据目录已回退到系统盘'
      : '未找到可写的非系统盘，数据目录已回退到系统盘',
  };
}

export function configureDesktopDataDirectory(): DesktopDataDirectoryStatus {
  const selected = selectDesktopDataDirectory({
    configuredPath: process.env.TESTMASTER_DESKTOP_DATA_DIR,
    systemUserData: app.getPath('userData'),
  });
  app.setPath('userData', selected.path);
  currentStatus = selected;
  return selected;
}

export function getDesktopDataDirectoryStatus(): DesktopDataDirectoryStatus {
  return currentStatus ?? {
    path: app.getPath('userData'), source: 'system-fallback', isSystemDrive: true,
    warning: '数据目录尚未初始化',
  };
}
