const api = require('../../utils/api')
const { timeAgo } = require('../../utils/util')

Page({
  data: { notifications: [], loading: false },

  onLoad() { this.loadNotifications() },

  async loadNotifications() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/notifications')
      const notifications = (res.items || res || []).map(n => ({
        ...n,
        is_read: n.is_read || n.read || false,
        time: timeAgo(n.created_at)
      }))
      this.setData({ notifications, loading: false })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  async markRead(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.post(`/notifications/${id}/read`)
      this.loadNotifications()
    } catch (err) {
      console.error('标记已读失败', err)
    }
  },

  async markAllRead() {
    try {
      await api.post('/notifications/read-all')
      this.loadNotifications()
      wx.showToast({ title: '已全部标记为已读', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  }
})
