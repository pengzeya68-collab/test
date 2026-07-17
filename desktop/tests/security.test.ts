/**
 * Security settings test 鈥?Phase 0 gate.
 *
 * Verifies that the Electron window is created with the correct security
 * settings per Section 4.1 of the Implementation Spec.
 */

import { describe, it, expect } from 'vitest';
import * as path from 'path';
import { pathToFileURL } from 'url';
import { getSecurityConfig, _testIsAllowedOrigin } from '../src/main/window';

describe('Electron Security Settings', () => {
  it('should have contextIsolation enabled', () => {
    const config = getSecurityConfig();
    expect(config.contextIsolation).toBe(true);
  });

  it('should have nodeIntegration disabled', () => {
    const config = getSecurityConfig();
    expect(config.nodeIntegration).toBe(false);
  });

  it('should have sandbox enabled', () => {
    const config = getSecurityConfig();
    expect(config.sandbox).toBe(true);
  });

  it('should have webSecurity enabled', () => {
    const config = getSecurityConfig();
    expect(config.webSecurity).toBe(true);
  });

  it('should have allowRunningInsecureContent disabled', () => {
    const config = getSecurityConfig();
    expect(config.allowRunningInsecureContent).toBe(false);
  });
});

describe('Origin Allowlist', () => {
  it('should allow the approved dev origins only', () => {
    const origEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';
    expect(_testIsAllowedOrigin('http://localhost:5173')).toBe(true);
    expect(_testIsAllowedOrigin('http://127.0.0.1:5173')).toBe(true);
    expect(_testIsAllowedOrigin('http://localhost:5001')).toBe(false);
    process.env.NODE_ENV = origEnv;
  });

  it('should block untrusted origins', () => {
    const origEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';
    expect(_testIsAllowedOrigin('https://evil.example.com')).toBe(false);
    expect(_testIsAllowedOrigin('file:///etc/passwd')).toBe(false);
    process.env.NODE_ENV = origEnv;
  });

  it('should allow the packaged renderer path in production', () => {
    const rendererIndexUrl = pathToFileURL(path.resolve(__dirname, '../src/renderer/index.html')).toString();
    expect(_testIsAllowedOrigin(rendererIndexUrl)).toBe(true);
  });
});
