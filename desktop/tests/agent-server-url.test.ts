import { describe, expect, it } from 'vitest';
import { normalizeServerUrl } from '../src/main/desktop-agent-service';
import { assertHttpNavigationUrl } from '../src/shared/safe-url';

describe('desktop Agent server URL', () => {
  it('allows local HTTP backends', () => {
    expect(normalizeServerUrl('http://127.0.0.1:5001/')).toBe('http://127.0.0.1:5001');
    expect(normalizeServerUrl('http://localhost:5001/api')).toBe('http://localhost:5001');
  });

  it('requires HTTPS for remote agent registration', () => {
    expect(() => normalizeServerUrl('http://35.194.164.151/')).toThrow('REMOTE_AGENT_REQUIRES_HTTPS');
    expect(normalizeServerUrl('https://testmaster.example.com/api/health')).toBe('https://testmaster.example.com');
  });

  it('rejects unsupported schemes', () => {
    expect(() => normalizeServerUrl('ftp://testmaster.example.com')).toThrow('INVALID_SERVER_URL');
  });
});

describe('navigation URL safety', () => {
  it('rejects file:// and script schemes', () => {
    expect(() => assertHttpNavigationUrl('file:///etc/passwd')).toThrow(/blocked scheme/);
    expect(() => assertHttpNavigationUrl('javascript:alert(1)')).toThrow(/blocked scheme/);
  });

  it('accepts http(s) and data fixtures', () => {
    expect(assertHttpNavigationUrl('https://example.com/path')).toBe('https://example.com/path');
    expect(assertHttpNavigationUrl('http://127.0.0.1:3000/')).toBe('http://127.0.0.1:3000/');
    expect(assertHttpNavigationUrl('data:text/html,<h1>ok</h1>')).toContain('data:text/html');
  });
});
