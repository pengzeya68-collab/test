const api = require('../../utils/api')
const { debounce, timeAgo } = require('../../utils/util')

Page({
  data: {
    scenarios: [],
    environments: [],
    envIndex: 0,
    keyword: '',
    page: 1,
    hasMore: true,
    loading: false,
    running: false
  },

  onLoad() {
    this.loadEnvironments()
    this.loadScenarios()
  },

  onShow() {
    if (this.data.scenarios.length > 0) {
      this.setData({ page: 1, scenarios: [], hasMore: true })
      this.loadScenarios()
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, scenarios: [], hasMore: true })
    this.loadScenarios()
    wx.stopPullDownRefresh()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadMore()
  },

  async loadEnvironments() {
    try {
      const res = await api.get('/environments', {}, { isAutoTest: true })
      const environments = res.items || res || []
      this.setData({ environments })
    } catch (err) {
      console.error('获取环境失败', err)
    }
  },

  onEnvChange(e) {
    this.setData({ envIndex: e.detail.value })
  },

  onSearch: debounce(function (e) {
    this.setData({ keyword: e.detail.value, page: 1, scenarios: [], hasMore: true })
    this.loadScenarios()
  }, 500),

  async loadScenarios() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const { keyword, page } = this.data
      const params = { page, page_size: 20 }
      if (keyword) params.search = keyword

      const res = await api.get('/scenarios', params, { isAutoTest: true })
      const items = (res.items || res || []).map(item => ({
        ...item,
        last_run: item.updated_at ? timeAgo(item.updated_at) : ''
      }))

      this.setData({
        scenarios: this.data.scenarios.concat(items),
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
    this.loadScenarios()
  },

  async runScenario(e) {
    const { id, name } = e.currentTarget.dataset
    const { environments, envIndex } = this.data
    const envId = environments[envIndex] ? environments[envIndex].id : null

    const confirmRes = await new Promise(resolve => {
      wx.showModal({
        title: '确认执行',
        content: `确定要执行场景「${name}」吗？${envId ? '\n环境: ' + environments[envIndex].name : ''}`,
        success: resolve
      })
    })

    if (!confirmRes.confirm) return

    this.setData({ running: true })
    wx.showLoading({ title: '启动中...' })

    try {
      const body = {}
      if (envId) body.environment_id = envId

      const res = await api.post(`/scenarios/${id}/run`, body, { isAutoTest: true })
      wx.hideLoading()

      const taskId = res.task_id || res.id
      wx.showToast({ title: '已启动执行', icon: 'success' })

      setTimeout(() => {
        wx.navigateTo({ url: `/pages/autotest/task-status?id=${taskId}&name=${encodeURIComponent(name)}` })
      }, 500)
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '启动失败', icon: 'none' })
    } finally {
      this.setData({ running: false })
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/autotest/scenario-detail?id=${id}` })
  },

  goHistory(e) {
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/autotest/history?scenarioId=${id}` })
    } else {
      wx.navigateTo({ url: '/pages/autotest/history' })
    }
  }
})
