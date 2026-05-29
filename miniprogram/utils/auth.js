const CONFIG = require('./config')

function getToken() {
  const app = getApp()
  if (app && app.globalData.token) {
    return app.globalData.token
  }
  return wx.getStorageSync(CONFIG.TOKEN_KEY)
}

function setToken(token, refreshToken) {
  const app = getApp()
  if (app) app.globalData.token = token
  wx.setStorageSync(CONFIG.TOKEN_KEY, token)
  if (refreshToken) {
    wx.setStorageSync(CONFIG.REFRESH_TOKEN_KEY, refreshToken)
  }
}

function getBaseUrl() {
  const app = getApp()
  if (app && app.globalData.baseUrl) {
    return app.globalData.baseUrl
  }
  return wx.getStorageSync(CONFIG.BASE_URL_KEY) || CONFIG.DEFAULT_BASE_URL
}

function setBaseUrl(url) {
  const app = getApp()
  if (app) app.globalData.baseUrl = url
  wx.setStorageSync(CONFIG.BASE_URL_KEY, url)
}

function clearAuth() {
  const app = getApp()
  if (app) {
    app.globalData.token = null
    app.globalData.userInfo = null
  }
  wx.removeStorageSync(CONFIG.TOKEN_KEY)
  wx.removeStorageSync(CONFIG.REFRESH_TOKEN_KEY)
  wx.removeStorageSync(CONFIG.USER_INFO_KEY)
}

function isLoggedIn() {
  return !!getToken()
}

function getUserInfo() {
  const app = getApp()
  if (app && app.globalData.userInfo) {
    return app.globalData.userInfo
  }
  return wx.getStorageSync(CONFIG.USER_INFO_KEY)
}

function setUserInfo(info) {
  const app = getApp()
  if (app) app.globalData.userInfo = info
  wx.setStorageSync(CONFIG.USER_INFO_KEY, info)
}

async function ensureLogin() {
  if (isLoggedIn()) return true
  return new Promise((resolve) => {
    wx.navigateTo({
      url: '/pages/login/login',
      success: () => resolve(false),
      fail: () => resolve(false)
    })
  })
}

module.exports = {
  getToken,
  setToken,
  getBaseUrl,
  setBaseUrl,
  clearAuth,
  isLoggedIn,
  getUserInfo,
  setUserInfo,
  ensureLogin
}
