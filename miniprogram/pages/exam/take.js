const api = require('../../utils/api')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: { exam: {}, questions: [], answers: {}, currentIndex: 0, timer: '', timerSeconds: 0, submitting: false, attemptId: '' },

  onLoad(options) {
    if (options && options.id) this.loadExam(options.id)
  },

  onUnload() {
    if (this._timerInterval) {
      clearInterval(this._timerInterval)
      this._timerInterval = null
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
      const attemptData = await api.post(`/api/v1/exams/${id}/start`)
      const attemptId = attemptData.id || attemptData.attempt_id || ''
      this.setData({ attemptId })
    } catch (err) {
      this.setData({ attemptId: '' })
    }

    try {
      const qData = await api.get(`/api/v1/exams/${id}/questions`)
      const list = Array.isArray(qData) ? qData : (qData?.items || qData?.questions || [])
      this.setData({ questions: list })
    } catch (err) {
      showToast('加载题目失败')
    }
    hideLoading()

    this.startTimer()
  },

  startTimer() {
    const duration = this.data.exam.duration || this.data.exam.time_limit || 0
    if (!duration) return

    let seconds = duration * 60
    this.setData({ timerSeconds: seconds })
    this._updateTimerDisplay(seconds)

    this._timerInterval = setInterval(() => {
      seconds--
      this.setData({ timerSeconds: seconds })
      this._updateTimerDisplay(seconds)

      if (seconds <= 0) {
        clearInterval(this._timerInterval)
        this._timerInterval = null
        showToast('考试时间到，自动提交')
        this.doSubmit()
      }
    }, 1000)
  },

  _updateTimerDisplay(seconds) {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    const pad = n => String(n).padStart(2, '0')
    this.setData({ timer: h > 0 ? `${pad(h)}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}` })
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
    if (this.data.submitting) return
    this.setData({ submitting: true })

    if (this._timerInterval) {
      clearInterval(this._timerInterval)
      this._timerInterval = null
    }

    try {
      const answerList = []
      for (const [idx, ans] of Object.entries(this.data.answers)) {
        answerList.push({
          question_id: this.data.questions[parseInt(idx)]?.id,
          answer: ans
        })
      }

      const { attemptId, exam } = this.data
      const submitId = attemptId || exam.id
      const data = await api.post(`/api/v1/exams/attempts/${submitId}/submit`, { answers: answerList })
      showToast('提交成功', 'success')
      wx.redirectTo({ url: `/pages/exam/result?attempt_id=${data.id || data.attempt_id || submitId}&score=${data.score || 0}` })
    } catch (err) {
      showToast(err.message || '提交失败')
    } finally {
      this.setData({ submitting: false })
    }
  }
})
