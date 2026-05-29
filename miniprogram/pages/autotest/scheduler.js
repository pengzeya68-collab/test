const api = require('../../utils/api')

Page({
  data: {
    tasks: [],
    loading: false
  },

  onLoad() { this.loadTasks() },
  onShow() { this.loadTasks() },

  async loadTasks() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/scheduler/tasks', {}, { isAutoTest: true })
      this.setData({ tasks: res.items || res || [], loading: false })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async triggerTask(e) {
    const { id, name } = e.currentTarget.dataset
    wx.showModal({
      title: '确认执行',
      content: `确定要立即执行「${name}」吗？`,
      success: async (res) => {
        if (!res.confirm) return
        wx.showLoading({ title: '启动中...' })
        try {
          const result = await api.post(`/scheduler/tasks/${id}/run`, {}, { isAutoTest: true })
          wx.hideLoading()
          wx.showToast({ title: '已启动', icon: 'success' })
        } catch (err) {
          wx.hideLoading()
          wx.showToast({ title: err.message || '启动失败', icon: 'none' })
        }
      }
    })
  },

  async toggleTask(e) {
    const { id, active } = e.currentTarget.dataset
    try {
      await api.post(`/scheduler/tasks/${id}/toggle`, { is_active: !active }, { isAutoTest: true })
      wx.showToast({ title: active ? '已暂停' : '已启用', icon: 'success' })
      this.loadTasks()
    } catch (err) {
      wx.showToast({ title: err.message || '操作失败', icon: 'none' })
    }
  },

  async deleteTask(e) {
    const { id, name } = e.currentTarget.dataset
    wx.showModal({
      title: '确认删除',
      content: `确定要删除定时任务「${name}」吗？`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/scheduler/tasks/${id}`, {}, { isAutoTest: true })
          wx.showToast({ title: '已删除', icon: 'success' })
          this.loadTasks()
        } catch (err) {
          wx.showToast({ title: err.message || '删除失败', icon: 'none' })
        }
      }
    })
  }
})
