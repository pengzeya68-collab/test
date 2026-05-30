const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: { activeTab: 'score', rankList: [], topList: [], loading: false },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.loadData()
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const tab = this.data.activeTab
      const data = await api.get(`/api/v1/leaderboard/${tab}`)
      const list = Array.isArray(data) ? data : (data?.items || data?.leaderboard || [])
      this.setData({ rankList: list, topList: list.slice(0, 3) })
    } catch (err) {
      this.setData({ rankList: [], topList: [] })
    } finally {
      this.setData({ loading: false })
    }
  }
})
