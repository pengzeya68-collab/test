const api = require('../../utils/api')
const { getDifficultyTag } = require('../../utils/util')

Page({
  data: {
    exercise: {},
    options: [],
    selectedOption: -1,
    correctIndex: -1,
    submitted: false,
    isCorrect: false,
    difficultyTag: { text: '', cls: '' }
  },

  onLoad(options) {
    if (options.id) {
      this.loadExercise(options.id)
    }
  },

  async loadExercise(id) {
    wx.showLoading({ title: '加载中' })
    try {
      const res = await api.get(`/exercises/${id}`)
      const exercise = res
      const options = this.parseOptions(exercise)
      const correctIndex = this.findCorrectIndex(exercise, options)

      this.setData({
        exercise,
        options,
        correctIndex,
        difficultyTag: getDifficultyTag(exercise.difficulty)
      })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  parseOptions(exercise) {
    const labels = ['A', 'B', 'C', 'D', 'E', 'F']
    const options = []

    if (exercise.options && Array.isArray(exercise.options)) {
      exercise.options.forEach((opt, i) => {
        options.push({
          label: labels[i],
          text: typeof opt === 'string' ? opt : (opt.text || opt.content || '')
        })
      })
    } else {
      const fields = ['option_a', 'option_b', 'option_c', 'option_d']
      fields.forEach((f, i) => {
        if (exercise[f]) {
          options.push({ label: labels[i], text: exercise[f] })
        }
      })
    }

    return options
  },

  findCorrectIndex(exercise, options) {
    const correct = exercise.correct_answer || exercise.answer || ''
    const labels = ['A', 'B', 'C', 'D', 'E', 'F']
    if (typeof correct === 'number') return correct
    const upper = String(correct).toUpperCase().trim()
    return labels.indexOf(upper)
  },

  selectOption(e) {
    if (this.data.submitted) return
    this.setData({ selectedOption: e.currentTarget.dataset.index })
  },

  async submitAnswer() {
    if (this.data.selectedOption === -1) {
      wx.showToast({ title: '请选择答案', icon: 'none' })
      return
    }

    const labels = ['A', 'B', 'C', 'D', 'E', 'F']
    const answer = labels[this.data.selectedOption]

    this.setData({ submitted: true, isCorrect: this.data.selectedOption === this.data.correctIndex })

    try {
      await api.post('/exercise/submit', {
        exercise_id: this.data.exercise.id,
        solution: answer
      })
    } catch (err) {
      console.error('提交失败', err)
    }
  },

  nextExercise() {
    wx.navigateBack()
  }
})
