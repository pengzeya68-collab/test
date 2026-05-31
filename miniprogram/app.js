const { BASE_URL } = require('./utils/config')

App({
  globalData: {
    baseUrl: BASE_URL,
    userInfo: null,
    token: null
  },

  onLaunch: function () {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    if (token && userInfo) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
    }
  }
})
