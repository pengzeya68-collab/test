export function safeJsonParse(str, fallback = null) {
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

// JWT 格式校验：三个 base64url 段用 . 连接
const JWT_PATTERN = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/

export function isValidTokenFormat(token) {
  return typeof token === 'string' && JWT_PATTERN.test(token)
}

export const TOKEN_KEY = 'token'
export const USER_KEY = 'user'
export const ADMIN_TOKEN_KEY = 'admin_token'
export const ADMIN_INFO_KEY = 'admin_info'
export const ASSESSMENT_KEY = 'assessment_completed'
export const SKILL_PROFILE_KEY = 'skill_profile'

export function isAdminRoute() {
  // 兼容 Hash 模式和 History 模式路由
  const path = window.location.hash ? window.location.hash.replace('#', '') : window.location.pathname
  return path.startsWith('/admin')
}

export function getToken() {
  return getUserToken()
}

export function getAuthToken() {
  return getAdminToken()
}

export function getUserToken() {
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token || !isValidTokenFormat(token)) {
      return null
    }
    return token
  } catch {
    return null
  }
}

export function getAdminToken() {
  try {
    const token = localStorage.getItem(ADMIN_TOKEN_KEY)
    if (!token || !isValidTokenFormat(token)) {
      return null
    }
    return token
  } catch {
    return null
  }
}

export function setToken(newToken) {
  if (!newToken) return
  localStorage.setItem(TOKEN_KEY, newToken)
}

export function setUserInfo(user) {
  if (user) {
    // 仅缓存非敏感字段，敏感数据通过 API 获取
    const safeUser = {
      id: user.id,
      username: user.username,
      avatar: user.avatar,
      level: user.level,
      score: user.score,
      is_admin: user.is_admin,
    }
    localStorage.setItem(USER_KEY, JSON.stringify(safeUser))
  }
}

export function setAdminToken(token) {
  if (!token) return
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export function setAdminInfo(info) {
  if (info) {
    // 仅缓存非敏感字段
    const safeInfo = {
      id: info.id,
      username: info.username,
      avatar: info.avatar,
      is_admin: info.is_admin,
      is_super_admin: info.is_super_admin,
    }
    localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(safeInfo))
  }
}

export function clearAllAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_INFO_KEY)
  localStorage.removeItem(ASSESSMENT_KEY)
  localStorage.removeItem(SKILL_PROFILE_KEY)
}

export function clearUserAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(ASSESSMENT_KEY)
  localStorage.removeItem(SKILL_PROFILE_KEY)
}

export function clearAdminAuth() {
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_INFO_KEY)
}
