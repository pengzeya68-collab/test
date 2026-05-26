export const TOKEN_KEY = 'token'
export const USER_KEY = 'user'
export const ADMIN_TOKEN_KEY = 'admin_token'
export const ADMIN_INFO_KEY = 'admin_info'
export const ASSESSMENT_KEY = 'assessment_completed'
export const SKILL_PROFILE_KEY = 'skill_profile'

export function isAdminRoute() {
  const hash = window.location.hash
  return hash.startsWith('#/admin')
}

export function getToken() {
  return getUserToken() || getAdminToken()
}

export function getAuthToken() {
  return getAdminToken() || getUserToken()
}

export function getUserToken() {
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token || token === 'undefined' || token === 'null' || token === '[object Object]') {
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
    if (!token || token === 'undefined' || token === 'null' || token === '[object Object]') {
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
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

export function setAdminToken(token) {
  if (!token) return
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export function setAdminInfo(info) {
  if (info) {
    localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(info))
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

const authUtil = {
  isAdminRoute,
  getToken,
  getAuthToken,
  getUserToken,
  getAdminToken,
  setToken,
  setUserInfo,
  setAdminToken,
  setAdminInfo,
  clearAllAuth,
  clearUserAuth,
  clearAdminAuth,
  TOKEN_KEY,
  USER_KEY,
  ADMIN_TOKEN_KEY,
  ADMIN_INFO_KEY,
  ASSESSMENT_KEY,
  SKILL_PROFILE_KEY,
}

export default authUtil
