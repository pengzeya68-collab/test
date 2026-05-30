const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: {
    allList: [],
    list: [],
    activeTab: 'all',
    loading: false
  },

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
    this.filterList()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/auto-test/history')
      const allList = Array.isArray(data) ? data : (data?.items || data?.history || [])
      this.setData({ allList })
      this.filterList()
    } catch (err) {
      this.setData({ allList: [], list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  filterList() {
    const { allList, activeTab } = this.data
    let list = allList
    if (activeTab !== 'all') {
      list = allList.filter(i => i.status === activeTab)
    }
    this.setData({ list })
  }
})
