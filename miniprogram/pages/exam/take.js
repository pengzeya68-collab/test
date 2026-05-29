const api = require('../../utils/api')

Page({
  data: {
    exam: {},
    examId: '',
    questions: [],
    currentQuestion: {},
    currentIndex: 0,
    answers: [],
    attemptId: '',
    timeLeft: 3600,
    timeDisplay: '60:00',
    timer: null
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ examId: options.id })
      this.loadExam(options.id)
    }
  },

  onUnload() {
    if (this.data.timer) clearInterval(this.data.timer)
  },

  async loadExam(id) {
    wx.showLoading({ title: '加载中' })
    try {
      // Step 1: get exam detail
      const detail = await api.get(`/exams/${id}`)
      this.setData({ exam: detail })

      // Step 2: start exam to get questions and attempt_id
      const startRes = await api.post(`/exams/${id}/start`)
      const questions = this.parseQuestions(startRes.questions || [])
      this.setData({
        questions,
        currentQuestion: questions[0] || {},
        answers: new Array(questions.length).fill(-1),
        attemptId: startRes.attempt_id || startRes.id
      })

      if (detail.duration) {
        this.setData({ timeLeft: detail.duration * 60 })
      }
      this.startTimer()
    } catch (err) {
      // Fallback: try GET questions endpoint
      try {
        const qRes = await api.get(`/exams/${id}/questions`)
        const questions = this.parseQuestions(qRes.questions || [])
        this.setData({
          exam: qRes,
          questions,
          currentQuestion: questions[0] || {},
          answers: new Array(questions.length).fill(-1),
          attemptId: qRes.attempt_id || qRes.id || ''
        })
        if (qRes.duration) {
          this.setData({ timeLeft: qRes.duration * 60 })
        }
        this.startTimer()
      } catch (err2) {
        wx.showToast({ title: '加载失败', icon: 'none' })
      }
    } finally {
      wx.hideLoading()
    }
  },

  parseQuestions(raw) {
    const labels = ['A', 'B', 'C', 'D', 'E', 'F']
    return raw.map(q => {
      const options = []
      if (q.options && Array.isArray(q.options)) {
        q.options.forEach((opt, i) => {
          options.push({ label: labels[i], text: typeof opt === 'string' ? opt : (opt.text || opt.content || '') })
        })
      } else {
        const fields = ['option_a', 'option_b', 'option_c', 'option_d']
        fields.forEach((f, i) => {
          if (q[f]) options.push({ label: labels[i], text: q[f] })
        })
      }
      return { ...q, options }
    })
  },

  startTimer() {
    const timer = setInterval(() => {
      const timeLeft = this.data.timeLeft - 1
      if (timeLeft <= 0) {
        clearInterval(timer)
        this.submitExam()
        return
      }
      const mins = Math.floor(timeLeft / 60)
      const secs = timeLeft % 60
      this.setData({
        timeLeft,
        timeDisplay: `${mins}:${secs < 10 ? '0' + secs : secs}`
      })
    }, 1000)
    this.setData({ timer })
  },

  selectAnswer(e) {
    const index = e.currentTarget.dataset.index
    const answers = [...this.data.answers]
    answers[this.data.currentIndex] = index
    this.setData({ answers })
  },

  prevQuestion() {
    if (this.data.currentIndex > 0) {
      const currentIndex = this.data.currentIndex - 1
      this.setData({ currentIndex, currentQuestion: this.data.questions[currentIndex] })
    }
  },

  nextQuestion() {
    if (this.data.currentIndex < this.data.questions.length - 1) {
      const currentIndex = this.data.currentIndex + 1
      this.setData({ currentIndex, currentQuestion: this.data.questions[currentIndex] })
    }
  },

  async submitExam() {
    const unanswered = this.data.answers.filter(a => a === -1).length
    if (unanswered > 0) {
      const res = await new Promise(resolve => {
        wx.showModal({
          title: '提示',
          content: `还有 ${unanswered} 题未作答，确定交卷吗？`,
          success: resolve
        })
      })
      if (!res.confirm) return
    }

    if (this.data.timer) clearInterval(this.data.timer)

    wx.showLoading({ title: '提交中...' })
    try {
      const labels = ['A', 'B', 'C', 'D', 'E', 'F']
      const answersObj = {}
      this.data.answers.forEach((ans, i) => {
        const q = this.data.questions[i]
        if (ans >= 0 && q && q.id) {
          answersObj[q.id] = labels[ans]
        }
      })

      const res = await api.post(`/exams/attempts/${this.data.attemptId}/submit`, {
        exam_id: this.data.examId,
        answers: answersObj
      })

      wx.hideLoading()
      const resultId = res.attempt_id || res.id || this.data.attemptId
      wx.redirectTo({ url: `/pages/exam/result?attemptId=${resultId}` })
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '提交失败', icon: 'none' })
    }
  }
})
