const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: { list: [], activeTab: 'available', loading: false },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.loadData()
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab, list: [] })
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      if (this.data.activeTab === 'available') {
        const data = await api.get('/api/v1/exams')
        const list = Array.isArray(data) ? data : (data?.items || [])
        this.setData({ list })
      } else {
        const data = await api.get('/api/v1/exams/my-attempts')
        const list = Array.isArray(data) ? data : (data?.items || [])
        this.setData({ list })
      }
    } catch (err) {
      this.setData({ list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  goExam(e) {
    const id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: `/pages/exam/take?id=${id}` })
  }
})
