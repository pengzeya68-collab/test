const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: {
    allList: [],
    list: [],
    activeTab: 'all',
    loading: false,
    noMore: false,
    page: 1,
    pageSize: 20
  },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.setData({ page: 1, noMore: false })
    this.loadData()
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
    this.filterList()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/auto-test/history', { page: 1, page_size: this.data.pageSize })
      const allList = Array.isArray(data) ? data : (data?.items || data?.history || [])
      this.setData({ allList, noMore: allList.length < this.data.pageSize })
      this.filterList()
    } catch (err) {
      this.setData({ allList: [], list: [], noMore: true })
      showToast('加载历史记录失败')
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
  },

  loadMore() {
    if (this.data.noMore || this.data.loading) return
    const nextPage = this.data.page + 1
    this.setData({ page: nextPage, loading: true })

    api.get('/api/auto-test/history', { page: nextPage, page_size: this.data.pageSize })
      .then(data => {
        const moreList = Array.isArray(data) ? data : (data?.items || data?.history || [])
        const existingIds = new Set(this.data.allList.map(i => i.id))
        const newItems = moreList.filter(i => !existingIds.has(i.id))
        const allList = [...this.data.allList, ...newItems]
        this.setData({
          allList,
          noMore: moreList.length < this.data.pageSize,
          loading: false
        })
        this.filterList()
      })
      .catch(() => {
        this.setData({ loading: false })
        showToast('加载更多失败')
      })
  }
})
