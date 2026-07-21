import { describe, expect, it } from 'vitest';
import { selectDesktopDataDirectory } from '../src/main/desktop-data-directory';

describe('desktop data directory selection', () => {
  it('uses an explicit writable absolute directory first', () => {
    const selected = selectDesktopDataDirectory({
      configuredPath: 'E:\\CompanyData\\TestMaster',
      systemUserData: 'C:\\Users\\tester\\AppData\\Roaming\\TestMaster',
      platform: 'win32', systemDrive: 'C:', driveRoots: ['D:\\'], ensureWritable: value => value.startsWith('E:'),
    });
    expect(selected.source).toBe('configured');
    expect(selected.path).toBe('E:\\CompanyData\\TestMaster');
    expect(selected.isSystemDrive).toBe(false);
  });

  it('prefers the first writable non-system drive', () => {
    const selected = selectDesktopDataDirectory({
      systemUserData: 'C:\\Users\\tester\\AppData\\Roaming\\TestMaster',
      platform: 'win32', systemDrive: 'C:', driveRoots: ['D:\\', 'E:\\'],
      driveExists: () => true,
      ensureWritable: value => value.startsWith('D:'),
    });
    expect(selected).toMatchObject({ source: 'non-system-drive', path: 'D:\\TestMasterData', isSystemDrive: false, warning: null });
  });

  it('falls back to userData and returns a visible warning', () => {
    const systemUserData = 'C:\\Users\\tester\\AppData\\Roaming\\TestMaster';
    const selected = selectDesktopDataDirectory({
      systemUserData, platform: 'win32', systemDrive: 'C:', driveRoots: ['D:\\'],
      driveExists: () => true,
      ensureWritable: value => value === systemUserData,
    });
    expect(selected.source).toBe('system-fallback');
    expect(selected.path).toBe(systemUserData);
    expect(selected.warning).toContain('系统盘');
  });
});
