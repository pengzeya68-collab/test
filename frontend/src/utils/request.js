import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const service = axios.create({
  baseURL,
  timeout: 10000
})

const setToken = (newToken) => {
  localStorage.setItem('token', newToken)
  service.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
}

let isLoggingOut = false

service.interceptors.request.use(
  config => {
    let token = localStorage.getItem('admin_token')
    if (!token || token === 'undefined' || token === 'null' || token === '[object Object]') {
      token = localStorage.getItem('token')
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
  error => {
    if (!error.response) {
      return Promise.reject(error)
    }

    const { status, config } = error.response

    if (status === 401) {
      if (isLoggingOut) {
        return Promise.reject(error)
      }

      isLoggingOut = true

      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')
      localStorage.removeItem('skill_profile')
      localStorage.removeItem('assessment_completed')

      ElMessage.error('登录已过期，请重新登录')
      router.push('/login')

      setTimeout(() => { isLoggingOut = false }, 1000)
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)

export default service
export { setToken }
