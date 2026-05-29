const api = require('../../utils/api')

Page({
  data: { exams: [], loading: false },

  onLoad() { this.loadExams() },

  async loadExams() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/exams')
      this.setData({ exams: res.items || res || [], loading: false })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  goExam(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/exam/take?id=${id}` })
  }
})
