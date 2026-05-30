const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: { list: [], unlockedCount: 0, totalCount: 0, loading: false },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/v1/achievements/')
      const list = Array.isArray(data) ? data : (data?.items || data?.achievements || [])
      const unlockedCount = list.filter(i => i.unlocked || i.is_unlocked).length
      this.setData({ list, unlockedCount, totalCount: list.length })
    } catch (err) {
      this.setData({ list: [] })
    } finally {
      this.setData({ loading: false })
    }
  }
})
