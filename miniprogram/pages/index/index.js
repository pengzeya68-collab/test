const api = require('../../utils/api')
const auth = require('../../utils/auth')

Page({
  data: {
    userInfo: {},
    greeting: '',
    stats: { exerciseCount: 0, completedCount: 0, streakDays: 0 },
    recentExercises: [],
    dailyExercise: {}
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
    this.setData({ userInfo })
    this.loadData()
  },

  async loadData() {
    try {
      const exercises = await api.get('/api/v1/exercises')
      const list = (exercises || []).slice(0, 5)
      this.setData({
        recentExercises: list,
        stats: {
          exerciseCount: (exercises || []).length,
          completedCount: 0,
          streakDays: 0
        },
        dailyExercise: list[0] || {}
      })
    } catch (err) {
      console.error('加载首页数据失败:', err)
    }

    try {
      const progress = await api.get('/api/v1/exercise/progress')
      if (progress && typeof progress === 'object') {
        this.setData({
          'stats.completedCount': progress.completed_count || progress.completedCount || 0,
          'stats.streakDays': progress.streak_days || progress.streakDays || 0
        })
      }
    } catch (err) {
      // progress接口可能未部署，静默处理
    }

    try {
      const me = await api.get('/api/v1/auth/me')
      if (me && typeof me === 'object') {
        this.setData({
          'stats.exerciseCount': me.score || this.data.stats.exerciseCount
        })
      }
    } catch (err) {
      // 静默处理
    }
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
