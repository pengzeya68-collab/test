const { getApiUrl } = require('./config')

let isRedirecting = false

function getToken() {
  return wx.getStorageSync('token') || ''
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
