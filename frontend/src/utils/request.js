import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 从环境变量读取 API 基础路径，开发环境下由于 proxy 的存在，可以使用 /api，但生产环境建议使用环境变量
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const service = axios.create({
  baseURL: baseURL,
  timeout: 10000
})

// Request interceptor
service.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token（优先 admin_token，其次 token）
    let token = localStorage.getItem('admin_token');
    if (!token || token === 'undefined' || token === 'null' || token === '[object Object]') {
      token = localStorage.getItem('token');
    }
    // 必须严格判断，绝不能把字符串 'undefined' / 'null' / '[object Object]' 发过去！
    if (token && token !== 'undefined' && token !== 'null' && token !== '[object Object]') {
      // 只有真正有效的token才附加到请求头
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
)

// Response interceptor
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 401(没有token) → 清除token并跳转登录
          ElMessage.error('登录已过期，请重新登录')
          // 判断是后台接口还是前台接口
          if (error.config.url?.includes('/admin/')) {
            localStorage.removeItem('admin_token')
            localStorage.removeItem('admin_info')
            router.push('/admin/login')
          } else {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(error.response.data?.error || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default service
