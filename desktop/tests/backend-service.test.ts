import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { persistentDesktopPassword, readLocalBackendCredentials, resolveDesktopJMeterRuntime } from '../src/main/backend-service';

describe('bundled local backend credentials', () => {
  it('creates a stable local-only password and reads it back', () => {
    const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'testmaster-credentials-'));
    try {
      const first = persistentDesktopPassword(dataDir);
      const second = persistentDesktopPassword(dataDir);
      expect(first).toHaveLength(24);
      expect(second).toBe(first);
      expect(readLocalBackendCredentials(dataDir)).toEqual({ username: 'admin', password: first });
    } finally {
      fs.rmSync(dataDir, { recursive: true, force: true });
    }
  });

  it('does not return weak or missing credentials', () => {
    const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'testmaster-credentials-'));
    try {
      expect(readLocalBackendCredentials(dataDir)).toBeNull();
      fs.writeFileSync(path.join(dataDir, '.desktop-admin-password'), 'too-short');
      expect(readLocalBackendCredentials(dataDir)).toBeNull();
    } finally {
      fs.rmSync(dataDir, { recursive: true, force: true });
    }
  });
});

describe('desktop JMeter runtime resolution', () => {
  it('uses an explicitly configured executable and keeps reports in desktop data', () => {
    const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'testmaster-jmeter-'));
    const binDir = path.join(dataDir, 'jmeter', 'bin');
    const executable = path.join(binDir, 'jmeter.bat');
    fs.mkdirSync(binDir, { recursive: true });
    fs.writeFileSync(executable, '');
    try {
      expect(resolveDesktopJMeterRuntime(dataDir, { JMETER_BIN: executable }, 'win32')).toEqual({
        JMETER_ENGINE_ENABLED: 'true',
        JMETER_HOME: path.join(dataDir, 'jmeter'),
        JMETER_BIN: executable,
        JMETER_REPORT_DIR: path.join(dataDir, 'jmeter-reports'),
      });
    } finally {
      fs.rmSync(dataDir, { recursive: true, force: true });
    }
  });

  it('honours an explicit disable switch even when the executable exists', () => {
    const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'testmaster-jmeter-'));
    const executable = path.join(dataDir, 'jmeter.bat');
    fs.writeFileSync(executable, '');
    try {
      expect(resolveDesktopJMeterRuntime(dataDir, {
        JMETER_BIN: executable,
        JMETER_ENGINE_ENABLED: 'false',
      }, 'win32')).toEqual({
        JMETER_ENGINE_ENABLED: 'false',
        JMETER_REPORT_DIR: path.join(dataDir, 'jmeter-reports'),
      });
    } finally {
      fs.rmSync(dataDir, { recursive: true, force: true });
    }
  });
});
