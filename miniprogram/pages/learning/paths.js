const api = require('../../utils/api')

Page({
  data: { paths: [], loading: false },

  onLoad() { this.loadPaths() },

  async loadPaths() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/learning-paths')
      const paths = (res.items || res || []).map(p => ({
        ...p,
        progress: p.progress !== undefined ? Math.round(p.progress) : 0
      }))
      this.setData({ paths, loading: false })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/learning/path-detail?id=${id}` })
  }
})
