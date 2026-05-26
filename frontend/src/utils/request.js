import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { getToken, getAuthToken, clearAllAuth, isAdminRoute, setToken as saveToken } from '@/utils/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const service = axios.create({
  baseURL,
  timeout: 10000
})

const setToken = (newToken) => {
  saveToken(newToken)
  service.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
}

let isLoggingOut = false

const syncClientAuthState = async () => {
  clearAllAuth()

  try {
    const [{ useUserStore }, { useAdminStore }] = await Promise.all([
      import('@/stores/user'),
      import('@/stores/admin')
    ])

    useUserStore().resetSession()
    useAdminStore().resetSession()
  } catch {
    // Stores may be unavailable during very early app bootstrap.
  }
}

service.interceptors.request.use(
  config => {
    const isAdminReq = config.url?.startsWith('/admin') || 
                      config.url?.startsWith('/autotest')
    
    let token = null
    if (isAdminReq) {
      token = getAuthToken()
    } else {
      token = getToken()
    }
    
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

service.interceptors.response.use(
  response => response.data,
  async error => {
    if (!error.response) {
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
      await syncClientAuthState()

      ElMessage.error('登录已过期，请重新登录')
      
      if (isAdminRoute()) {
        router.push('/admin/login')
      } else {
        router.push('/login')
      }

      setTimeout(() => { isLoggingOut = false }, 1000)
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)

export default service
export { setToken }
