/**
 * 后台权限控制工具
 */

import { ElMessage } from 'element-plus'

// Token存储key（和主项目保持一致
const ADMIN_TOKEN_KEY = 'admin_token'
const USER_INFO_KEY = 'admin_info'
const NORMAL_TOKEN_KEY = 'token'
const NORMAL_USER_KEY = 'user'

/**
 * 获取管理员Token
 */
export const getAdminToken = () => {
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

/**
 * 存储管理员Token
 */
export const setAdminToken = (token) => {
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

/**
 * 移除管理员Token
 */
export const removeAdminToken = () => {
  localStorage.removeItem(ADMIN_TOKEN_KEY)
}

/**
 * 获取用户信息
 */
export const getUserInfo = () => {
  const userInfo = localStorage.getItem(USER_INFO_KEY)
  return userInfo ? JSON.parse(userInfo) : null
}

/**
 * 判断是否是管理员
 */
export const isAdmin = () => {
  const userInfo = getUserInfo()
  return userInfo?.is_admin === true
}

/**
 * 检查是否已登录
 */
export const isLoggedIn = () => {
  return !!getAdminToken()
}

/**
 * 退出登录
 */
export const logout = () => {
  removeAdminToken()
  localStorage.removeItem(USER_INFO_KEY)
}

/**
 * 设置后台路由守卫
 * @param router Vue Router实例
 */
export const setupAdminGuard = (router) => {
  // 路由守卫已经在主路由里配置了，这里不需要重复配置
}

/**
 * 请求拦截器 - 自动携带管理员Token
 */
export const adminRequestInterceptor = (config) => {
  const token = getAdminToken()
  if (token && config.url?.startsWith('/api/admin/')) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

/**
 * 响应拦截器 - 处理权限错误
 */
export const adminResponseInterceptor = (response) => {
  if (response.config.url?.startsWith('/api/admin/')) {
    // Token过期或无效
    if (response.data.code === 401) {
      logout()
      ElMessage.error('登录已过期，请重新登录')
      window.location.href = '/#/admin/login'
    }
    
    // 权限不足
    if (response.data.code === 403) {
      ElMessage.error('您没有权限执行此操作')
    }
  }
  return response
}
