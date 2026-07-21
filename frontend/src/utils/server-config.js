const SERVER_URL_KEY = 'testmaster_server_url'
const DEFAULT_SERVER_URL = 'http://127.0.0.1:5001'
const isDesktop = import.meta.env.VITE_DESKTOP_BUILD === 'true'

export function normalizeServerUrl(value) {
  return String(value || DEFAULT_SERVER_URL).trim().replace(/\/+$/, '')
}

export function getServerUrl() {
  return normalizeServerUrl(localStorage.getItem(SERVER_URL_KEY) || import.meta.env.VITE_SERVER_URL || DEFAULT_SERVER_URL)
}

export function setServerUrl(value) {
  const normalized = normalizeServerUrl(value)
  let parsed
  try { parsed = new URL(normalized) } catch { throw new Error('服务地址格式不正确') }
  const isLocal = ['127.0.0.1', 'localhost'].includes(parsed.hostname)
  if (!isDesktop && !isLocal && parsed.protocol !== 'https:') throw new Error('企业服务地址必须使用 HTTPS')
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('服务地址只支持 HTTP 或 HTTPS')
  localStorage.setItem(SERVER_URL_KEY, normalized)
  return normalized
}
