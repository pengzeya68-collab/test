import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@app-router'
import { getUserToken, getAdminToken, clearUserAuth, clearAdminAuth } from '@/utils/auth'
import { getServerUrl } from '@/utils/server-config'

const isDesktop = import.meta.env.VITE_DESKTOP_BUILD === 'true'
const webApiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const webAutoTestBase = import.meta.env.VITE_AUTO_TEST_BASE_URL || '/api'
const apiBaseURL = () => isDesktop ? `${getServerUrl()}/api/v1` : webApiBase
const autoTestBaseURL = () => isDesktop ? `${getServerUrl()}/api` : webAutoTestBase

const service = axios.create({ timeout: 15000 })
const autoTestService = axios.create({ timeout: 120000 })

const applyToken = (config, baseURL) => {
  config.baseURL = baseURL
  config.headers = config.headers || {}
  const isAdminRequest = String(config.url || '').startsWith('/admin/')
  const token = isAdminRequest ? getAdminToken() : getUserToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  else delete config.headers.Authorization
  return config
}
service.interceptors.request.use(config => applyToken(config, apiBaseURL()))
autoTestService.interceptors.request.use(config => applyToken(config, autoTestBaseURL()))

const unwrap = response => response.data
const onError = (error) => {
  const status = error.response?.status
  const detail = error.response?.data?.detail
  const isAdminRequest = String(error.config?.url || '').startsWith('/admin/')
  if (typeof detail === 'string') error.message = detail
  if (status === 401) {
    if (isAdminRequest) clearAdminAuth()
    else clearUserAuth()
    ElMessage.error('登录已失效，请重新登录')
    router.push(isAdminRequest ? '/admin/login' : '/login')
  } else if (status === 403) {
    ElMessage.error(typeof detail === 'string' ? detail : '没有权限执行此操作')
  } else if (!error.response) {
    error.message = '无法连接 TestMaster 服务'
  }
  return Promise.reject(error)
}
service.interceptors.response.use(unwrap, onError)
autoTestService.interceptors.response.use(unwrap, onError)

export const setToken = token => {
  if (!token) return
  service.defaults.headers.common.Authorization = `Bearer ${token}`
  autoTestService.defaults.headers.common.Authorization = `Bearer ${token}`
}
export const setAdminTokenHeader = token => {
  if (!token) return
  service.defaults.headers.common.Authorization = `Bearer ${token}`
}
export const clearTokenHeader = () => {
  delete service.defaults.headers.common.Authorization
  delete autoTestService.defaults.headers.common.Authorization
}
export const restoreActiveTokenHeader = () => {
  const token = getUserToken()
  if (token) setToken(token)
  else clearTokenHeader()
}
export const autoTestRequest = autoTestService
export default service
