const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: {
    recentTasks: [],
    scenarios: [],
    loading: true
  },

  onLoad() {},

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 })
    }
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    let recentTasks = []
    let scenarios = []

    try {
      const data = await api.get('/api/auto-test/history')
      if (Array.isArray(data)) {
        recentTasks = data
      } else if (data && Array.isArray(data.items)) {
        recentTasks = data.items
      } else if (data && Array.isArray(data.history)) {
        recentTasks = data.history
      }
    } catch (err) {
      console.error('加载历史失败:', err.message)
    }

    try {
      const data = await api.get('/api/auto-test/scenarios')
      if (Array.isArray(data)) {
        scenarios = data
      } else if (data && Array.isArray(data.items)) {
        scenarios = data.items
      } else if (data && Array.isArray(data.scenarios)) {
        scenarios = data.scenarios
      }
    } catch (err) {
      console.error('加载场景失败:', err.message)
    }

    this.setData({
      recentTasks: recentTasks.slice(0, 5),
      scenarios: scenarios.slice(0, 5),
      loading: false
    })
  },

  async runScenario(e) {
    const id = e.currentTarget.dataset.id
    const name = e.currentTarget.dataset.name
    if (!id) { showToast('场景ID异常'); return }

    wx.showModal({
      title: '确认运行',
      content: `是否运行场景「${name}」？`,
      success: async (res) => {
        if (res.confirm) {
          showLoading('正在启动...')
          try {
            await api.post(`/api/auto-test/scenarios/${id}/run`)
            showToast('场景已启动', 'success')
            setTimeout(() => this.loadData(), 2000)
          } catch (err) {
            showToast(err.message || '启动失败')
          } finally {
            hideLoading()
          }
        }
      }
    })
  },

  goScenarios() { wx.navigateTo({ url: '/pages/autotest/scenarios' }) },
  goCases() { wx.navigateTo({ url: '/pages/autotest/cases' }) },
  goHistory() { wx.navigateTo({ url: '/pages/autotest/history' }) },
  goScheduler() { wx.navigateTo({ url: '/pages/autotest/scheduler' }) }
})
