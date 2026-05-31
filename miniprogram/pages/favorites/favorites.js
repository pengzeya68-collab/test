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
      const data = await api.get('/api/v1/favorites')
      const list = Array.isArray(data) ? data : (data?.items || [])
      this.setData({ list })
    } catch (err) {
      this.setData({ list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  async unfavorite(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.post('/api/v1/favorites/toggle', { exercise_id: id })
      const list = this.data.list.filter(item => item.id !== id)
      this.setData({ list })
      showToast('已取消收藏')
    } catch (err) {
      showToast(err.message || '操作失败')
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  }
})
