const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: {
    userInfo: {},
    greeting: '',
    stats: { exerciseCount: 0, completedCount: 0, streakDays: 0, score: 0 },
    recentExercises: [],
    dailyExercise: {},
    loading: true,
    loadError: false
  },

  onLoad() {
    const hour = new Date().getHours()
    let greeting = '晚上好'
    if (hour < 12) greeting = '早上好'
    else if (hour < 18) greeting = '下午好'
    this.setData({ greeting })
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 })
    }
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    const userInfo = auth.getUserInfo() || {}
    this.setData({ userInfo, loading: true, loadError: false })
    this.loadData()
  },

  async loadData() {
    let hasError = false

    try {
      const exercises = await api.get('/api/v1/exercises')
      const list = (exercises || []).slice(0, 5)
      const totalCount = Array.isArray(exercises) ? exercises.length : (exercises?.items?.length || 0)
      this.setData({
        recentExercises: list,
        'stats.exerciseCount': totalCount
      })
    } catch (err) {
      if (err.message === '登录已过期') return
      hasError = true
    }

    try {
      const progress = await api.get('/api/v1/exercise/progress')
      if (progress && typeof progress === 'object') {
        this.setData({
          'stats.completedCount': progress.completed_count || progress.completedCount || 0,
          'stats.streakDays': progress.streak_days || progress.streakDays || 0,
          'stats.score': progress.score || 0
        })
      }
    } catch (err) {
      if (err.message === '登录已过期') return
      hasError = true
    }

    try {
      const dailyData = await api.get('/api/v1/exercise/daily-tasks')
      const dailyList = Array.isArray(dailyData) ? dailyData : (dailyData?.items || dailyData?.tasks || [])
      if (dailyList.length > 0) {
        this.setData({ dailyExercise: dailyList[0] })
      }
    } catch (err) {
      if (!this.data.dailyExercise.id && this.data.recentExercises.length > 0) {
        this.setData({ dailyExercise: this.data.recentExercises[0] })
      }
    }

    try {
      const me = await api.get('/api/v1/auth/me')
      if (me && typeof me === 'object') {
        this.setData({
          'stats.score': me.score || this.data.stats.score
        })
      }
    } catch (err) {
      if (err.message === '登录已过期') return
    }

    this.setData({ loading: false, loadError: hasError })
  },

  goExerciseList() { wx.switchTab({ url: '/pages/exercise/list' }) },
  goAutotest() { wx.switchTab({ url: '/pages/autotest/index' }) },
  goExamList() { wx.navigateTo({ url: '/pages/exam/list' }) },
  goWrongAnswers() { wx.navigateTo({ url: '/pages/exercise/wrong' }) },
  goLearningPaths() { wx.navigateTo({ url: '/pages/learning/paths' }) },
  goExerciseDetail(e) {
    const id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  },
  goProfile() { wx.switchTab({ url: '/pages/profile/profile' }) }
})
