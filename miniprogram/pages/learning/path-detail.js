const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showLoading, hideLoading, showToast } = require('../../utils/util')

Page({
  data: { path: {}, exercises: [], progress: {}, loadError: false },

  onLoad(options) {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    if (options && options.id) {
      this.loadData(options.id)
    } else {
      this.setData({ loadError: true })
      showToast('缺少路径ID')
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  async loadData(id) {
    showLoading('加载中...')
    try {
      const data = await api.get(`/api/v1/learning-paths/${id}`)
      this.setData({ path: data })
      wx.setNavigationBarTitle({ title: data.name || data.title || '学习路径' })
    } catch (err) {
      this.setData({ loadError: true })
      showToast('加载路径失败')
    }

    try {
      const exData = await api.get(`/api/v1/learning-paths/${id}/exercises`)
      const list = Array.isArray(exData) ? exData : (exData?.items || [])
      this.setData({ exercises: list })
    } catch (err) { }

    try {
      const pData = await api.get(`/api/v1/learning-paths/${id}/progress`)
      if (pData) this.setData({ progress: pData })
    } catch (err) { }

    hideLoading()
  },

  goExercise(e) {
    const id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  }
})
