const api = require('./api')

function isLoggedIn() {
  return !!wx.getStorageSync('token')
}

function getUserInfo() {
  return wx.getStorageSync('userInfo') || null
}

function login(username, password) {
  return api.post('/api/v1/auth/login', { username, password }).then(res => {
    wx.setStorageSync('token', res.access_token)
    if (res.refresh_token) {
      wx.setStorageSync('refreshToken', res.refresh_token)
    }
    if (res.user) {
      wx.setStorageSync('userInfo', res.user)
    }
    return res
  })
}

function register(data) {
  return api.post('/api/v1/auth/register', data).then(res => {
    wx.setStorageSync('token', res.access_token)
    if (res.refresh_token) {
      wx.setStorageSync('refreshToken', res.refresh_token)
    }
    if (res.user) {
      wx.setStorageSync('userInfo', res.user)
    }
    return res
  })
}

function logout() {
  const refreshToken = wx.getStorageSync('refreshToken')
  return api.post('/api/v1/auth/logout', { refresh_token: refreshToken }).catch(() => {}).finally(() => {
    wx.removeStorageSync('token')
    wx.removeStorageSync('refreshToken')
    wx.removeStorageSync('userInfo')
  })
}

function checkLogin() {
  if (!isLoggedIn()) {
    wx.reLaunch({ url: '/pages/login/login' })
    return false
  }
  return true
}

module.exports = {
  isLoggedIn,
  getUserInfo,
  login,
  register,
  logout,
  checkLogin
}
