const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: { list: [], loading: false },

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
      const data = await api.get('/api/auto-test/scheduler/tasks')
      const list = Array.isArray(data) ? data : (data?.items || data?.tasks || [])
      this.setData({ list })
    } catch (err) {
      this.setData({ list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  async toggleTask(e) {
    const id = e.currentTarget.dataset.id
    const enabled = e.currentTarget.dataset.enabled
    showLoading('操作中...')
    try {
      await api.post(`/api/auto-test/scheduler/tasks/${id}/toggle`)
      showToast(enabled ? '已停用' : '已启用', 'success')
      this.loadData()
    } catch (err) {
      showToast(err.message || '操作失败')
    } finally {
      hideLoading()
    }
  },

  async runTask(e) {
    const id = e.currentTarget.dataset.id
    showLoading('启动中...')
    try {
      await api.post(`/api/auto-test/scheduler/tasks/${id}/run`)
      showToast('已触发执行', 'success')
    } catch (err) {
      showToast(err.message || '触发失败')
    } finally {
      hideLoading()
    }
  }
})
