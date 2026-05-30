const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: { score: 0, attemptId: '', result: null, loading: true },

  onLoad(options) {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    const score = options.score || 0
    const attemptId = options.attempt_id || ''
    this.setData({ score: parseInt(score), attemptId })
    if (attemptId) {
      this.loadResult(attemptId)
    } else {
      this.setData({ loading: false })
    }
  },

  async loadResult(attemptId) {
    try {
      const data = await api.get(`/api/v1/exams/attempts/${attemptId}`)
      if (data) {
        this.setData({
          result: data,
          score: data.score || this.data.score,
          loading: false
        })
      }
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  goBack() { wx.navigateBack({ delta: 2 }) }
})
