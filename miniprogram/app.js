// app.js
App({
  globalData: {
    baseUrl: 'https://34.150.26.84',
    userInfo: null,
    token: null
  },

  onLaunch: function () {
    // 检查本地存储的登录状态
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    if (token && userInfo) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
    }
  }
})
