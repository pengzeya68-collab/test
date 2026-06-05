import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { getUserToken, getAdminToken, clearAllAuth, clearUserAuth, clearAdminAuth, isAdminRoute, setToken as saveToken, isValidTokenFormat } from '@/utils/auth'

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

const setToken = (newToken) => {
  saveToken(newToken)
  service.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  autoTestService.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
}

let isLoggingOut = false

const syncClientAuthState = async () => {
  clearAllAuth()

  try {
    const [{ useUserStore }, { useAdminStore }] = await Promise.all([
      import('@/stores/user'),
      import('@/stores/admin'),
    ])

    useUserStore().resetSession()
    useAdminStore().resetSession()
  } catch (error) {
    console.warn('重置客户端状态失败:', error)
  }
}

// 请求拦截器：严格按路由选择 token，不 fallback
const requestInterceptor = (config) => {
  const isAdminReq = config.url?.startsWith('/admin') ||
                     config.url?.startsWith('/autotest') ||
                     config.url?.startsWith('/auto-test')

  const token = isAdminReq ? getAdminToken() : getUserToken()

  if (token && isValidTokenFormat(token)) {
    config.headers['Authorization'] = `Bearer ${token}`
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
      return Promise.reject(error)
    }

    isLoggingOut = true

    // 根据请求 URL 判断是管理员请求还是用户请求，只清除对应会话
    const isAdminReq = config.url?.startsWith('/admin') ||
                       config.url?.startsWith('/autotest') ||
                       config.url?.startsWith('/auto-test')

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

    ElMessage.error('登录已过期，请重新登录')

    // 根据请求来源决定跳转目标
    if (isAdminReq) {
      router.push('/admin/login')
    } else {
      router.push('/login')
    }

    setTimeout(() => { isLoggingOut = false }, 1000)
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
export { setToken, autoTestRequest }
