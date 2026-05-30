const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: { exam: {}, questions: [], answers: {}, currentIndex: 0, timer: '', submitting: false },

  onLoad(options) {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    if (options && options.id) {
      this.loadExam(options.id)
    } else {
      showToast('缺少考试ID')
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  async loadExam(id) {
    showLoading('加载中...')
    try {
      const data = await api.get(`/api/v1/exams/${id}`)
      this.setData({ exam: data })
      wx.setNavigationBarTitle({ title: data.title || '考试' })
    } catch (err) {
      showToast('加载考试失败')
      hideLoading()
      return
    }

    try {
      const qData = await api.get(`/api/v1/exams/${id}/questions`)
      const list = Array.isArray(qData) ? qData : (qData?.items || qData?.questions || [])
      this.setData({ questions: list })
    } catch (err) {
      showToast('加载题目失败')
    }
    hideLoading()
  },

  selectAnswer(e) {
    const key = e.currentTarget.dataset.key
    const idx = this.data.currentIndex
    this.setData({ [`answers.${idx}`]: key })
  },

  onAnswerInput(e) {
    const idx = this.data.currentIndex
    this.setData({ [`answers.${idx}`]: e.detail.value })
  },

  prevQuestion() {
    if (this.data.currentIndex > 0) {
      this.setData({ currentIndex: this.data.currentIndex - 1 })
    }
  },

  nextQuestion() {
    if (this.data.currentIndex < this.data.questions.length - 1) {
      this.setData({ currentIndex: this.data.currentIndex + 1 })
    }
  },

  async submitExam() {
    const { answers, questions } = this.data
    const unanswered = questions.filter((_, i) => !answers[i]).length
    if (unanswered > 0) {
      wx.showModal({
        title: '提示',
        content: `还有 ${unanswered} 题未作答，确定提交？`,
        success: async (res) => {
          if (res.confirm) this.doSubmit()
        }
      })
    } else {
      this.doSubmit()
    }
  },

  async doSubmit() {
    this.setData({ submitting: true })
    try {
      const answerList = []
      for (const [idx, ans] of Object.entries(this.data.answers)) {
        answerList.push({
          question_id: this.data.questions[parseInt(idx)]?.id,
          answer: ans
        })
      }
      const data = await api.post(`/api/v1/exams/${this.data.exam.id}/submit`, { answers: answerList })
      showToast('提交成功', 'success')
      wx.redirectTo({ url: `/pages/exam/result?attempt_id=${data.id || data.attempt_id || ''}&score=${data.score || 0}` })
    } catch (err) {
      showToast(err.message || '提交失败')
    } finally {
      this.setData({ submitting: false })
    }
  }
})
