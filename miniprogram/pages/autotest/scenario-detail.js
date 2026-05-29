const api = require('../../utils/api')

Page({
  data: {
    scenario: {},
    steps: [],
    environments: [],
    envIndex: 0
  },

  onLoad(options) {
    if (options.id) {
      this.loadScenario(options.id)
      this.loadSteps(options.id)
    }
    this.loadEnvironments()
  },

  async loadScenario(id) {
    wx.showLoading({ title: '加载中' })
    try {
      const res = await api.get(`/scenarios/${id}`, {}, { isAutoTest: true })
      this.setData({ scenario: res })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  async loadSteps(id) {
    try {
      const res = await api.get(`/scenarios/${id}`, {}, { isAutoTest: true })
      this.setData({ steps: res.steps || [] })
    } catch (err) {
      console.error('获取步骤失败', err)
    }
  },

  async loadEnvironments() {
    try {
      const res = await api.get('/environments', {}, { isAutoTest: true })
      this.setData({ environments: res.items || res || [] })
    } catch (err) {
      console.error('获取环境失败', err)
    }
  },

  async runScenario() {
    const { scenario, environments, envIndex } = this.data
    const envId = environments[envIndex] ? environments[envIndex].id : null

    wx.showModal({
      title: '确认执行',
      content: `确定要执行「${scenario.name}」吗？`,
      success: async (res) => {
        if (!res.confirm) return
        wx.showLoading({ title: '启动中...' })
        try {
          const body = {}
          if (envId) body.environment_id = envId
          const result = await api.post(`/scenarios/${scenario.id}/run`, body, { isAutoTest: true })
          wx.hideLoading()
          const taskId = result.task_id || result.id
          wx.navigateTo({ url: `/pages/autotest/task-status?id=${taskId}&name=${encodeURIComponent(scenario.name)}` })
        } catch (err) {
          wx.hideLoading()
          wx.showToast({ title: err.message || '启动失败', icon: 'none' })
        }
      }
    })
  },

  goHistory() {
    wx.navigateTo({ url: `/pages/autotest/history?scenarioId=${this.data.scenario.id}` })
  }
})
