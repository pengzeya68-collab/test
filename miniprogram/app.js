const { login, checkLogin } = require('./utils/auth')

App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: '',
    systemInfo: null
  },

  onLaunch() {
    const info = wx.getSystemInfoSync()
    this.globalData.systemInfo = info

    const savedToken = wx.getStorageSync('access_token')
    const savedBaseUrl = wx.getStorageSync('base_url')
    if (savedToken) {
      this.globalData.token = savedToken
    }
    if (savedBaseUrl) {
      this.globalData.baseUrl = savedBaseUrl
    }

    if (!this.globalData.baseUrl) {
      wx.navigateTo({ url: '/pages/login/login?mode=setup' })
    }
  }
})
