const api = require('../../utils/api')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: {
    exercise: {},
    userAnswer: '',
    userSql: '',
    submitResult: null,
    sqlResult: null,
    submitting: false,
    executing: false,
    isChoiceType: false,
    isMultipleChoice: false,
    isSqlType: false,
    choiceOptions: [],
    selectedChoice: '',
    selectedChoices: [],
    correctAnswerKey: '',
    correctAnswerKeys: [],
    loaded: false,
    loadError: false
  },

  onLoad(options) {
    if (options && options.id) {
      this.loadExercise(options.id)
    } else {
      this.setData({ loadError: true })
      showToast('缺少习题ID')
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  async loadExercise(id) {
    showLoading('加载中...')
    try {
      const data = await api.get(`/api/v1/exercises/${id}`)
      if (!data || !data.id) {
        this.setData({ loadError: true })
        showToast('习题不存在')
        return
      }
      this.setData({ exercise: data, loaded: true, loadError: false })
      wx.setNavigationBarTitle({ title: data.title || '练习详情' })
      this.detectQuestionType(data)
    } catch (err) {
      this.setData({ loadError: true })
      showToast('加载练习题失败: ' + (err.message || ''))
    } finally {
      hideLoading()
    }
  },

  detectQuestionType(exercise) {
    const type = (exercise.exercise_type || '').toLowerCase()
    const lang = (exercise.language || '').toLowerCase()

    if (type === 'multiple_choice') {
      this.parseChoiceOptions(exercise)
      this.setData({ isChoiceType: true, isMultipleChoice: true, isSqlType: false })
    } else if (type === 'single_choice') {
      this.parseChoiceOptions(exercise)
      this.setData({ isChoiceType: true, isMultipleChoice: false, isSqlType: false })
    } else if (lang === 'sql' || type === 'sql') {
      this.setData({ isChoiceType: false, isMultipleChoice: false, isSqlType: true })
    } else {
      this.setData({ isChoiceType: false, isMultipleChoice: false, isSqlType: false })
    }
  },

  parseChoiceOptions(exercise) {
    const desc = exercise.description || ''
    const options = []

    const lines = desc.split('\n')
    for (const line of lines) {
      const m = line.trim().match(/^([A-Z])[\.、\)\s]+(.+)$/)
      if (m) {
        options.push({ key: m[1], text: m[2].trim() })
      }
    }

    this.setData({ choiceOptions: options })
  },

  selectChoice(e) {
    if (this.data.submitResult) return
    const key = e.currentTarget.dataset.key

    if (this.data.isMultipleChoice) {
      const selectedChoices = this.data.selectedChoices.slice()
      const idx = selectedChoices.indexOf(key)
      if (idx >= 0) {
        selectedChoices.splice(idx, 1)
      } else {
        selectedChoices.push(key)
      }
      selectedChoices.sort()
      this.setData({ selectedChoices })
    } else {
      this.setData({ selectedChoice: key })
    }
  },

  onAnswerInput(e) { this.setData({ userAnswer: e.detail.value }) },
  onSqlInput(e) { this.setData({ userSql: e.detail.value }) },

  async submitAnswer() {
    const { exercise, selectedChoice, selectedChoices, userAnswer, userSql, isChoiceType, isMultipleChoice, submitting } = this.data
    if (submitting) return
    if (!exercise || !exercise.id) {
      showToast('习题数据异常')
      return
    }

    let solution = ''
    if (isChoiceType) {
      if (isMultipleChoice) {
        if (selectedChoices.length === 0) { showToast('请至少选择一个答案'); return }
        solution = selectedChoices.join(',')
      } else {
        if (!selectedChoice) { showToast('请先选择一个答案'); return }
        solution = selectedChoice
      }
    } else {
      solution = userSql || userAnswer
      if (!solution || !solution.trim()) { showToast('请先输入答案'); return }
    }

    this.setData({ submitting: true })
    try {
      const data = await api.post('/api/v1/exercises/submit', {
        exercise_id: exercise.id,
        solution: solution
      })

      let correctAnswerKey = ''
      let correctAnswerKeys = []
      if (data.expected_solution && typeof data.expected_solution === 'string') {
        const trimmed = data.expected_solution.trim()
        if (/^[A-Z]$/.test(trimmed)) {
          correctAnswerKey = trimmed
          correctAnswerKeys = [trimmed]
        } else {
          const keys = trimmed.split(/[,，\s]+/).filter(k => /^[A-Z]$/.test(k))
          if (keys.length > 0) {
            correctAnswerKeys = keys
            correctAnswerKey = keys.join(',')
          }
        }
      }

      this.setData({
        submitResult: data,
        correctAnswerKey: correctAnswerKey,
        correctAnswerKeys: correctAnswerKeys
      })

      if (data.correct) {
        showToast('🎉 回答正确！', 'success')
      } else {
        showToast('回答错误，再想想', 'none')
      }
    } catch (err) {
      showToast(err.message || '提交失败')
    } finally {
      this.setData({ submitting: false })
    }
  },

  async executeSql() {
    const { exercise, userSql, executing } = this.data
    if (executing) return
    if (!userSql || !userSql.trim()) { showToast('请输入SQL语句'); return }

    this.setData({ executing: true })
    try {
      const data = await api.post('/api/v1/exercises/execute-sql', {
        setup_sql: exercise.setup_sql || '',
        user_sql: userSql
      })
      this.setData({ sqlResult: data })
    } catch (err) {
      showToast(err.message || '执行失败')
    } finally {
      this.setData({ executing: false })
    }
  },

  retryExercise() {
    this.setData({
      submitResult: null,
      sqlResult: null,
      selectedChoice: '',
      selectedChoices: [],
      userAnswer: '',
      userSql: '',
      correctAnswerKey: '',
      correctAnswerKeys: []
    })
  },

  goNext() {
    wx.navigateBack()
  }
})
