const api = require('../../utils/api')
const { formatTime, getStatusTag } = require('../../utils/util')

Page({
  data: {
    records: [],
    filter: 'all',
    scenarioId: '',
    page: 1,
    hasMore: true,
    loading: false
  },

  onLoad(options) {
    if (options.scenarioId) {
      this.setData({ scenarioId: options.scenarioId })
    }
    this.loadHistory()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, records: [], hasMore: true })
    this.loadHistory()
    wx.stopPullDownRefresh()
  },

  setFilter(e) {
    const filter = e.currentTarget.dataset.val
    this.setData({ filter, page: 1, records: [], hasMore: true })
    this.loadHistory()
  },

  async loadHistory() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const { scenarioId, filter, page } = this.data
      const params = { page, page_size: 20 }
      if (scenarioId) params.scenario_id = scenarioId

      const res = await api.get('/history', params, { isAutoTest: true })
      let items = res.items || res || []

      if (filter !== 'all') {
        items = items.filter(item => {
          const s = (item.status || item.state || '').toLowerCase()
          return filter === 'success' ? s.includes('success') : s.includes('fail')
        })
      }

      const records = items.map(item => ({
        ...item,
        statusTag: getStatusTag(item.status || item.state),
        start_time: formatTime(item.start_time || item.created_at)
      }))

      this.setData({
        records: this.data.records.concat(records),
        hasMore: items.length >= 20,
        loading: false
      })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadHistory()
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/autotest/task-status?id=${id}` })
  }
})
