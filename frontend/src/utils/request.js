import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { getUserToken, getAdminToken, clearUserAuth, clearAdminAuth, setToken as saveToken, isValidTokenFormat } from '@/utils/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL
const AUTO_TEST_BASE_URL = import.meta.env.VITE_AUTO_TEST_BASE_URL || '/api'

if (!baseURL) {
  console.warn('[request] VITE_API_BASE_URL 未设置，使用默认值 /api/v1')
}

const service = axios.create({
  baseURL: baseURL || '/api/v1',
  timeout: 15000,
})

// 创建独立的 autoTest 实例，避免重复配置
const autoTestService = axios.create({
  baseURL: AUTO_TEST_BASE_URL,
  timeout: 120000,
})

const clearTokenHeader = () => {
  delete service.defaults.headers.common['Authorization']
  delete autoTestService.defaults.headers.common['Authorization']
}

/** 恢复仍有效的身份token到axios默认header */
const restoreActiveTokenHeader = () => {
  const userToken = getUserToken()
  const adminToken = getAdminToken()
  const token = userToken || adminToken
  if (token && isValidTokenFormat(token)) {
    service.defaults.headers.common['Authorization'] = `Bearer ${token}`
    autoTestService.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }
}

const setToken = (newToken) => {
  saveToken(newToken)
  service.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  autoTestService.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
}

/** 设置管理员token到axios实例header（不写入用户token键） */
const setAdminTokenHeader = (newToken) => {
  if (newToken && isValidTokenFormat(newToken)) {
    service.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    autoTestService.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }
}

let isLoggingOut = false

// 请求拦截器：根据请求来源选择 token
// /admin 路径使用管理员token；其他路径（包括/auto-test）优先使用用户token
const requestInterceptor = (config) => {
  const isAdminReq = config.url?.startsWith('/admin')

  let token
  if (isAdminReq) {
    token = getAdminToken()
  } else {
    // 用户页面请求仅使用用户token，不fallback到管理员token
    // 避免用户token过期后以管理员身份继续操作
    token = getUserToken()
  }

  if (token && isValidTokenFormat(token)) {
    config.headers['Authorization'] = `Bearer ${token}`
  } else {
    delete config.headers['Authorization']
  }
  return config
}

service.interceptors.request.use(requestInterceptor, (error) => Promise.reject(error))
autoTestService.interceptors.request.use(requestInterceptor, (error) => Promise.reject(error))

// 响应拦截器：统一错误处理
const responseErrorInterceptor = async (error) => {
  if (!error.response) {
    ElMessage.error('网络连接异常，请检查网络')
    return Promise.reject(error)
  }

  const { status, config } = error.response

  if (status === 401) {
    if (config?.skipAuthError) {
      return Promise.reject(error)
    }

    if (isLoggingOut) {
      // 并发401：静默拒绝，避免重复弹窗和跳转
      return Promise.reject(error)
    }

    isLoggingOut = true

    // 根据请求 URL 判断是管理员请求还是用户请求，只清除对应会话
    const isAdminReq = config.url?.startsWith('/admin')

    try {
      if (isAdminReq) {
        clearAdminAuth()
        const { useAdminStore } = await import('@/stores/admin')
        useAdminStore().resetSession()
      } else {
        clearUserAuth()
        const { useUserStore } = await import('@/stores/user')
        useUserStore().resetSession()
      }
    } catch (err) {
      console.warn('重置客户端状态失败:', err)
    }

    // 清除已过期身份的header后，恢复另一方仍有效的token
    restoreActiveTokenHeader()

    ElMessage.error('登录已过期，请重新登录')

    // 根据请求来源决定跳转目标
    if (isAdminReq) {
      router.push('/admin/login')
    } else {
      router.push('/login')
    }

    setTimeout(() => { isLoggingOut = false }, 3000)
    return Promise.reject(error)
  }

  if (status === 403) {
    ElMessage.error('权限不足，无法执行此操作')
    return Promise.reject(error)
  }

  // 提取后端返回的错误信息
  const detail = error.response?.data?.detail
  if (detail) {
    error.message = detail
  }
  return Promise.reject(error)
}

service.interceptors.response.use((response) => response.data, responseErrorInterceptor)
autoTestService.interceptors.response.use((response) => response.data, responseErrorInterceptor)

// 导出 autoTestRequest，直接使用独立实例
const autoTestRequest = (config) => autoTestService(config)
;['get', 'delete', 'head', 'options'].forEach((method) => {
  autoTestRequest[method] = (url, config) => autoTestService({ ...config, method, url })
})
;['post', 'put', 'patch'].forEach((method) => {
  autoTestRequest[method] = (url, data, config) => autoTestService({ ...config, method, url, data })
})

export default service
export { setToken, setAdminTokenHeader, autoTestRequest, clearTokenHeader, restoreActiveTokenHeader }
