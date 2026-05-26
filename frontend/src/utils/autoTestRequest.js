import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { getToken, clearAllAuth, isAdminRoute } from '@/utils/auth'

const autoTestRequest = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

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

autoTestRequest.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

autoTestRequest.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    if (error.response?.status === 401) {
      if (isLoggingOut) {
        return Promise.reject(error)
      }

      isLoggingOut = true
      ElMessage.error('登录已过期，请重新登录')
      await syncClientAuthState()
      if (isAdminRoute()) {
        router.push('/admin/login')
      } else {
        router.push('/login')
      }

      setTimeout(() => { isLoggingOut = false }, 1000)
    }
    return Promise.reject(error)
  }
)

export default autoTestRequest
