const api = require('../../utils/api')

Page({
  data: { result: {} },

  onLoad(options) {
    if (options.attemptId) {
      this.loadResult(options.attemptId)
    } else if (options.examId) {
      this.loadResult(options.examId)
    }
  },

  async loadResult(attemptId) {
    try {
      const res = await api.get(`/exams/attempts/${attemptId}/result`)
      this.setData({ result: res })
    } catch (err) {
      console.error('获取结果失败', err)
    }
  },

  goBack() {
    wx.navigateBack({ delta: 2 })
  }
})
