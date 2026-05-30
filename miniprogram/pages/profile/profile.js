const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: {
    userInfo: {},
    stats: { exercises: 0, completed: 0, score: 0, streak: 0 },
    checkedIn: false,
    loading: true,
    loadError: false
  },

  onLoad() {
    this._mounted = true
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 3 })
    }

    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }

    const userInfo = auth.getUserInfo() || {}
    this.setData({ userInfo, loading: true, loadError: false })
    this.loadAllData()
  },

  async loadAllData() {
    let hasError = false

    try {
      const exercises = await api.get('/api/v1/exercises')
      if (!this._mounted) return
      const exerciseCount = Array.isArray(exercises) ? exercises.length : (exercises && exercises.items ? exercises.items.length : 0)
      this.setData({ 'stats.exercises': exerciseCount })
    } catch (err) {
      if (err.message === '登录已过期') return
      hasError = true
    }

    try {
      const progress = await api.get('/api/v1/exercise/progress')
      if (!this._mounted) return
      if (progress && typeof progress === 'object') {
        this.setData({
          'stats.completed': progress.completed_count || progress.completedCount || 0,
          'stats.score': progress.score || 0,
          'stats.streak': progress.streak_days || progress.streakDays || 0
        })
      }
    } catch (err) {
      if (err.message === '登录已过期') return
      hasError = true
    }

    try {
      const status = await api.get('/api/v1/checkin/status')
      if (!this._mounted) return
      if (status && typeof status === 'object') {
        this.setData({ checkedIn: !!status.checked_in || !!status.checkedIn })
      }
    } catch (err) {
      if (err.message === '登录已过期') return
    }

    this.setData({ loading: false, loadError: hasError })
  },

  onUnload() {
    this._mounted = false
  },

  retryLoad() {
    this.setData({ loading: true, loadError: false })
    this.loadAllData()
  },

  goCheckin() {
    if (this.data.checkedIn) {
      showToast('今天已签到', 'none')
      return
    }
    wx.showModal({
      title: '每日签到',
      content: '确认进行每日签到？',
      success: async (res) => {
        if (res.confirm) {
          showLoading('签到中...')
          try {
            await api.post('/api/v1/checkin/')
            showToast('签到成功！+10积分', 'success')
            this.setData({ checkedIn: true, 'stats.streak': this.data.stats.streak + 1 })
          } catch (err) {
            showToast(err.message || '签到失败')
          } finally {
            hideLoading()
          }
        }
      }
    })
  },

  goWrongAnswers() { wx.navigateTo({ url: '/pages/exercise/wrong' }) },
  goFavorites() { wx.navigateTo({ url: '/pages/favorites/favorites' }) },
  goNotes() { wx.navigateTo({ url: '/pages/notes/notes' }) },
  goLeaderboard() { wx.navigateTo({ url: '/pages/leaderboard/leaderboard' }) },
  goAchievements() { wx.navigateTo({ url: '/pages/achievements/achievements' }) },
  changePassword() { wx.navigateTo({ url: '/pages/password/password' }) },

  handleLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: async (res) => {
        if (res.confirm) {
          await auth.logout()
          wx.reLaunch({ url: '/pages/login/login' })
        }
      }
    })
  }
})
