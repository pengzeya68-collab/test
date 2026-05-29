const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: {
    userInfo: {},
    stats: { exercises: 0, streak: 0, score: 0 },
    unreadCount: 0
  },

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    this.loadUserInfo()
    this.loadStats()
    this.loadUnreadCount()
  },

  async loadUserInfo() {
    const info = auth.getUserInfo()
    if (info) {
      this.setData({ userInfo: info })
    } else {
      try {
        const res = await api.get('/auth/me')
        auth.setUserInfo(res)
        this.setData({ userInfo: res })
      } catch (err) {
        console.error('获取用户信息失败', err)
      }
    }
  },

  async loadStats() {
    try {
      const res = await api.get('/exercise/progress')
      const progressMap = res.progress || {}
      const completedCount = Object.values(progressMap).filter(p => p.completed).length
      const totalCount = Object.keys(progressMap).length
      this.setData({
        'stats.exercises': completedCount,
        'stats.score': res.total_score || 0
      })
    } catch (err) {
      console.error('获取统计失败', err)
    }
    try {
      const res = await api.get('/checkin/status')
      this.setData({ 'stats.streak': res.current_streak || res.streak || 0 })
    } catch (err) {
      console.error('获取签到状态失败', err)
    }
  },

  async loadUnreadCount() {
    try {
      const res = await api.get('/notifications/unread-count')
      this.setData({ unreadCount: res.count || 0 })
    } catch (err) {
      console.error('获取未读数失败', err)
    }
  },

  goPage(e) {
    wx.navigateTo({ url: e.currentTarget.dataset.url })
  },

  goSetup() {
    wx.navigateTo({ url: '/pages/login/login?mode=setup' })
  },

  handleLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          auth.clearAuth()
          wx.redirectTo({ url: '/pages/login/login' })
        }
      }
    })
  }
})
