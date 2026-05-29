const api = require('../../utils/api')
const { getStatusTag } = require('../../utils/util')

Page({
  data: {
    taskId: '',
    taskName: '',
    status: '',
    statusTag: { text: '加载中', cls: 'tag-pending' },
    progress: 0,
    currentStep: '',
    isRunning: false,
    isCompleted: false,
    taskResult: null,
    stepResults: [],
    pollTimer: null
  },

  onLoad(options) {
    this.setData({
      taskId: options.id,
      taskName: decodeURIComponent(options.name || '测试任务')
    })
    this.refreshStatus()
    this.startPolling()
  },

  onUnload() {
    this.stopPolling()
  },

  startPolling() {
    this.stopPolling()
    const timer = setInterval(() => {
      if (this.data.isRunning) {
        this.refreshStatus()
      } else {
        this.stopPolling()
      }
    }, 3000)
    this.setData({ pollTimer: timer })
  },

  stopPolling() {
    if (this.data.pollTimer) {
      clearInterval(this.data.pollTimer)
      this.setData({ pollTimer: null })
    }
  },

  async refreshStatus() {
    try {
      const res = await api.get(`/tasks/${this.data.taskId}`, {}, { isAutoTest: true })
      const status = res.state || res.status || ''
      const statusTag = getStatusTag(status)

      const isRunning = ['PENDING', 'PROGRESS', 'RUNNING', 'running', 'pending'].includes(status)
      const isCompleted = ['SUCCESS', 'FAILURE', 'REVOKED', 'success', 'failed', 'error', 'completed'].includes(status)

      let progress = 0
      let currentStep = ''
      let taskResult = null
      let stepResults = []

      if (res.result) {
        taskResult = res.result
        stepResults = res.result.steps || res.result.step_results || []
      }

      if (res.meta && res.meta.current) {
        progress = res.meta.current || 0
        currentStep = res.meta.step || ''
        if (res.meta.total) {
          progress = Math.round((progress / res.meta.total) * 100)
        }
      }

      if (isCompleted && taskResult) {
        progress = 100
      }

      this.setData({
        status,
        statusTag,
        progress,
        currentStep,
        isRunning,
        isCompleted,
        taskResult,
        stepResults
      })

      if (isCompleted) {
        this.stopPolling()
        if (status === 'SUCCESS' || status === 'success') {
          wx.showToast({ title: '执行完成！', icon: 'success' })
        } else if (status === 'FAILURE' || status === 'failed') {
          wx.showToast({ title: '执行失败', icon: 'none' })
        }
      }
    } catch (err) {
      console.error('获取任务状态失败', err)
    }
  },

  goHistory() {
    wx.navigateTo({ url: '/pages/autotest/history' })
  },

  rerun() {
    wx.navigateBack()
  }
})
