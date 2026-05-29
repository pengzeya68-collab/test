const CONFIG = require('./config')
const { getToken, getBaseUrl, setToken, clearAuth, ensureLogin } = require('./auth')

let refreshingPromise = null

function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    timeout,
    isAutoTest = false,
    skipAuth = false
  } = options

  const baseUrl = getBaseUrl()
  const prefix = isAutoTest ? CONFIG.API_PREFIX_AUTO : CONFIG.API_PREFIX_V1
  const fullUrl = `${baseUrl}${prefix}${url}`

  const requestHeader = {
    'Content-Type': 'application/json',
    ...header
  }

  if (!skipAuth) {
    const token = getToken()
    if (token) {
      requestHeader['Authorization'] = `Bearer ${token}`
    }
  }

  const requestTimeout = timeout || (isAutoTest ? CONFIG.AUTO_TEST_TIMEOUT : CONFIG.TIMEOUT)

  return new Promise((resolve, reject) => {
    wx.request({
      url: fullUrl,
      method,
      data,
      header: requestHeader,
      timeout: requestTimeout,
      success: (res) => {
        if (res.statusCode === 401) {
          handleUnauthorized().then(() => {
            const newToken = getToken()
            requestHeader['Authorization'] = `Bearer ${newToken}`
            wx.request({
              url: fullUrl,
              method,
              data,
              header: requestHeader,
              timeout: requestTimeout,
              success: (retryRes) => {
                handleResponse(retryRes, resolve, reject)
              },
              fail: (err) => reject(err)
            })
          }).catch(() => {
            clearAuth()
            wx.redirectTo({ url: '/pages/login/login' })
            reject(new Error('登录已过期，请重新登录'))
          })
          return
        }
        handleResponse(res, resolve, reject)
      },
      fail: (err) => {
        wx.showToast({ title: '网络连接失败', icon: 'none' })
        reject(err)
      }
    })
  })
}

function handleResponse(res, resolve, reject) {
  if (res.statusCode >= 200 && res.statusCode < 300) {
    resolve(res.data)
  } else if (res.data && res.data.detail) {
    const msg = typeof res.data.detail === 'string' ? res.data.detail : JSON.stringify(res.data.detail)
    reject(new Error(msg))
  } else {
    reject(new Error(`请求失败 (${res.statusCode})`))
  }
}

async function handleUnauthorized() {
  if (refreshingPromise) return refreshingPromise

  const refreshToken = wx.getStorageSync(CONFIG.REFRESH_TOKEN_KEY)
  if (!refreshToken) {
    throw new Error('No refresh token')
  }

  refreshingPromise = new Promise((resolve, reject) => {
    const baseUrl = getBaseUrl()
    wx.request({
      url: `${baseUrl}${CONFIG.API_PREFIX_V1}/auth/refresh`,
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.access_token) {
          setToken(res.data.access_token, res.data.refresh_token)
          resolve()
        } else {
          reject(new Error('Refresh failed'))
        }
      },
      fail: reject,
      complete: () => {
        refreshingPromise = null
      }
    })
  })

  return refreshingPromise
}

function get(url, data, options = {}) {
  return request({ url, method: 'GET', data, ...options })
}

function post(url, data, options = {}) {
  return request({ url, method: 'POST', data, ...options })
}

function put(url, data, options = {}) {
  return request({ url, method: 'PUT', data, ...options })
}

function del(url, data, options = {}) {
  return request({ url, method: 'DELETE', data, ...options })
}

module.exports = {
  request,
  get,
  post,
  put,
  del
}
