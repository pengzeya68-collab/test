const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { timeAgo, getStatusTag } = require('../../utils/util')

Page({
  data: {
    userInfo: {},
    checkedIn: false,
    stats: {
      exerciseCount: 0,
      correctRate: '0%',
      streak: 0,
      scenarioCount: 0
    },
    runningTasks: [],
    hasRunningTasks: false,
    recentActivities: []
  },

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    this.loadUserInfo()
    this.loadCheckinStatus()
    this.loadStats()
    this.loadRunningTasks()
    this.loadRecentActivities()
  },

  onPullDownRefresh() {
    this.loadCheckinStatus()
    this.loadStats()
    this.loadRunningTasks()
    wx.stopPullDownRefresh()
  },

  async loadUserInfo() {
    const info = auth.getUserInfo()
    if (info) {
      this.setData({ userInfo: info })
      return
    }
    try {
      const res = await api.get('/auth/me')
      auth.setUserInfo(res)
      this.setData({ userInfo: res })
    } catch (err) {
      console.error('获取用户信息失败', err)
    }
  },

  async loadCheckinStatus() {
    try {
      const res = await api.get('/checkin/status')
      this.setData({ checkedIn: res.checked_in_today || res.checked_in || false })
    } catch (err) {
      console.error('获取签到状态失败', err)
    }
  },

  async handleCheckin() {
    if (this.data.checkedIn) {
      wx.showToast({ title: '今天已签到', icon: 'none' })
      return
    }
    try {
      const res = await api.post('/checkin')
      this.setData({ checkedIn: true })
      wx.showToast({ title: res.message || '签到成功！', icon: 'success' })
      this.loadStats()
      this.loadCheckinStatus()
    } catch (err) {
      wx.showToast({ title: err.message || '签到失败', icon: 'none' })
    }
  },

  async loadStats() {
    try {
      const [exerciseRes, skillRes] = await Promise.allSettled([
        api.get('/exercise/progress'),
        api.get('/skills/progress')
      ])
      const stats = { ...this.data.stats }
      if (exerciseRes.status === 'fulfilled') {
        const progressMap = exerciseRes.value.progress || {}
        stats.exerciseCount = Object.values(progressMap).filter(p => p.completed).length
        stats.correctRate = Object.keys(progressMap).length > 0
          ? Math.round(Object.values(progressMap).filter(p => p.completed).length / Object.keys(progressMap).length * 100) + '%'
          : '0%'
      }
      if (skillRes.status === 'fulfilled') {
        const progress = skillRes.value.progress || []
        stats.streak = progress.length > 0 ? Math.round(progress.reduce((sum, p) => sum + p.current, 0) / progress.length) : 0
      }
      this.setData({ stats })
    } catch (err) {
      console.error('获取统计失败', err)
    }

    try {
      const res = await api.get('/scenarios', {}, { isAutoTest: true })
      const items = Array.isArray(res) ? res : (res.items || [])
      this.setData({ 'stats.scenarioCount': items.length || 0 })
    } catch (err) {
      console.error('获取场景数量失败', err)
    }
  },

  async loadRunningTasks() {
    try {
      const res = await api.get('/history', { limit: 5 }, { isAutoTest: true })
      const rawItems = Array.isArray(res) ? res : (res.items || [])
      const tasks = rawItems.filter(t =>
        ['PENDING', 'PROGRESS', 'RUNNING', 'running', 'pending'].includes(t.state || t.status || '')
      )
      const formattedTasks = tasks.slice(0, 3).map(t => ({
        id: t.task_id || t.id,
        name: t.scenario_name || t.name || '测试任务',
        start_time: timeAgo(t.start_time || t.created_at)
      }))
      this.setData({
        runningTasks: formattedTasks,
        hasRunningTasks: formattedTasks.length > 0
      })
    } catch (err) {
      this.setData({ runningTasks: [], hasRunningTasks: false })
    }
  },

  async loadRecentActivities() {
    try {
      const res = await api.get('/exercise/recent-activity')
      const activities = (res.activities || res || []).map(a => ({
        id: a.id,
        type: a.type || 'exercise',
        title: a.title || a.exercise_title || a.exercise_title || '练习',
        desc: a.description || a.result || '',
        time: timeAgo(a.created_at || a.timestamp)
      }))
      this.setData({ recentActivities: activities.slice(0, 5) })
    } catch (err) {
      console.error('获取最近活动失败', err)
    }
  },

  goPage(e) {
    const url = e.currentTarget.dataset.url
    if (url === '/pages/exercise/list' || url === '/pages/autotest/index' || url === '/pages/profile/profile') {
      wx.switchTab({ url })
    } else {
      wx.navigateTo({ url })
    }
  },

  goTaskStatus(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/autotest/task-status?id=${id}` })
  }
})
