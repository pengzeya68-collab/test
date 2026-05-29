const api = require('../../utils/api')

Page({
  data: { path: {}, lessons: [] },

  onLoad(options) {
    if (options.id) {
      this.loadPath(options.id)
      this.loadLessons(options.id)
    }
  },

  async loadPath(id) {
    try {
      const res = await api.get(`/learning-paths/${id}`)
      this.setData({ path: { ...res, progress: res.progress !== undefined ? Math.round(res.progress) : 0 } })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  async loadLessons(id) {
    try {
      const res = await api.get(`/learning-paths/${id}/lessons`)
      this.setData({ lessons: res.items || res || [] })
    } catch (err) {
      console.error('获取课时失败', err)
    }
  }
})
