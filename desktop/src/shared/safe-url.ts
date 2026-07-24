/**
 * Navigation / recorder URL safety helpers.
 * Blocks local-file and non-http(s) schemes that could leak disk content.
 */

const LOCAL_HOSTS = new Set(['127.0.0.1', 'localhost', '::1']);

export function isLocalHostname(hostname: string): boolean {
  const host = String(hostname || '').toLowerCase().replace(/^\[|\]$/g, '');
  return LOCAL_HOSTS.has(host) || host.endsWith('.localhost');
}

/**
 * Allow navigation to http(s), about:blank, and data: fixtures.
 * Blocks file:/javascript:/vbscript: which can read local disk or execute code.
 */
const ALLOWED_NAV_PROTOCOLS = new Set(['http:', 'https:', 'about:', 'data:']);
const BLOCKED_NAV_PROTOCOLS = new Set(['file:', 'javascript:', 'vbscript:', 'blob:']);

export function assertHttpNavigationUrl(raw: string, field = 'url'): string {
  const value = String(raw || '').trim();
  if (!value) throw new Error(`INVALID_${field.toUpperCase()}: empty`);
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    // Relative paths are resolved later against baseUrl; still reject dangerous schemes.
    const schemeMatch = value.match(/^([a-zA-Z][a-zA-Z0-9+.-]*):/);
    if (schemeMatch) {
      const scheme = `${schemeMatch[1].toLowerCase()}:`;
      if (BLOCKED_NAV_PROTOCOLS.has(scheme) || !ALLOWED_NAV_PROTOCOLS.has(scheme)) {
        throw new Error(`INVALID_${field.toUpperCase()}: blocked scheme ${scheme}`);
      }
    }
    return value;
  }
  if (BLOCKED_NAV_PROTOCOLS.has(parsed.protocol) || !ALLOWED_NAV_PROTOCOLS.has(parsed.protocol)) {
    throw new Error(`INVALID_${field.toUpperCase()}: blocked scheme ${parsed.protocol}`);
  }
  if (parsed.protocol === 'about:' && parsed.pathname !== 'blank' && parsed.href !== 'about:blank') {
    throw new Error(`INVALID_${field.toUpperCase()}: only about:blank is allowed`);
  }
  return value;
}

/**
 * Agent server URL: local may use http; remote must use https (agentKey is a long-lived secret).
 */
export function normalizeAgentServerUrl(value: string): string {
  const normalized = String(value || '').trim().replace(/\/+$/, '');
  let parsed: URL;
  try {
    parsed = new URL(normalized);
  } catch {
    throw new Error('INVALID_SERVER_URL');
  }
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('INVALID_SERVER_URL');
  }
  if (!isLocalHostname(parsed.hostname) && parsed.protocol !== 'https:') {
    throw new Error('REMOTE_AGENT_REQUIRES_HTTPS');
  }
  return parsed.origin;
}
