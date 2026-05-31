const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

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
      const data = await api.get('/api/v1/notifications')
      const list = Array.isArray(data) ? data : (data?.items || [])
      this.setData({ list })
    } catch (err) {
      this.setData({ list: [] })
      if (err.message !== '登录已过期') {
        showToast('加载通知失败')
      }
    } finally {
      this.setData({ loading: false })
    }
  },

  async readNotif(e) {
    const id = e.currentTarget.dataset.id
    const index = e.currentTarget.dataset.index
    try {
      await api.post(`/api/v1/notifications/${id}/read`)
      this.setData({
        [`list[${index}].is_read`]: true,
        [`list[${index}].read`]: true
      })
    } catch (err) {
      if (err.message !== '登录已过期') {
        showToast('标记失败')
      }
    }
  },

  async readAll() {
    try {
      await api.post('/api/v1/notifications/read-all')
      const list = this.data.list.map(i => ({ ...i, is_read: true, read: true }))
      this.setData({ list })
      showToast('已全部标记为已读', 'success')
    } catch (err) {
      showToast('操作失败')
    }
  }
})
