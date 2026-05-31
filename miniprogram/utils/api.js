const { getApiUrl } = require('./config')

let isRedirecting = false
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(cb => cb(newToken))
  refreshSubscribers = []
}

function getToken() {
  return wx.getStorageSync('token') || ''
}

function getRefreshToken() {
  return wx.getStorageSync('refreshToken') || ''
}

async function tryRefreshToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  try {
    const res = await new Promise((resolve, reject) => {
      wx.request({
        url: getApiUrl('/api/v1/auth/refresh'),
        method: 'POST',
        data: { refresh_token: refreshToken },
        header: { 'Content-Type': 'application/json' },
        success(res) {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data)
          } else {
            reject(new Error('刷新失败'))
          }
        },
        fail: reject
      })
    })

    if (res.access_token) {
      wx.setStorageSync('token', res.access_token)
      if (res.refresh_token) {
        wx.setStorageSync('refreshToken', res.refresh_token)
      }
      return res.access_token
    }
    return null
  } catch (err) {
    return null
  }
}

function request(options) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const header = {
      'Content-Type': 'application/json',
      ...(options.header || {})
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: getApiUrl(options.url),
      method: options.method || 'GET',
      data: options.data || {},
      header,
      success(res) {
        if (res.statusCode === 401) {
          if (options._isRetry) {
            wx.removeStorageSync('token')
            wx.removeStorageSync('refreshToken')
            wx.removeStorageSync('userInfo')
            if (!isRedirecting) {
              isRedirecting = true
              wx.reLaunch({
                url: '/pages/login/login',
                complete() { isRedirecting = false }
              })
            }
            reject(new Error('登录已过期'))
            return
          }

          if (!isRefreshing) {
            isRefreshing = true
            tryRefreshToken().then(newToken => {
              isRefreshing = false
              if (newToken) {
                onTokenRefreshed(newToken)
                const retryOptions = { ...options, _isRetry: true }
                request(retryOptions).then(resolve).catch(reject)
              } else {
                wx.removeStorageSync('token')
                wx.removeStorageSync('refreshToken')
                wx.removeStorageSync('userInfo')
                if (!isRedirecting) {
                  isRedirecting = true
                  wx.reLaunch({
                    url: '/pages/login/login',
                    complete() { isRedirecting = false }
                  })
                }
                reject(new Error('登录已过期'))
              }
            })
          } else {
            subscribeTokenRefresh(() => {
              const retryOptions = { ...options, _isRetry: true }
              request(retryOptions).then(resolve).catch(reject)
            })
          }
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          const errMsg = (res.data && (res.data.detail || res.data.message)) || `请求失败(${res.statusCode})`
          reject(new Error(errMsg))
        }
      },
      fail(err) {
        reject(new Error('网络连接失败'))
      }
    })
  })
}

function get(url, data) {
  return request({ url, method: 'GET', data })
}

function post(url, data) {
  return request({ url, method: 'POST', data })
}

function put(url, data) {
  return request({ url, method: 'PUT', data })
}

function del(url, data) {
  return request({ url, method: 'DELETE', data })
}

module.exports = {
  request,
  get,
  post,
  put,
  del
}
