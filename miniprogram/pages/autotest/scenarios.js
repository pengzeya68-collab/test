const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: {
    allList: [],
    list: [],
    keyword: '',
    loading: false
  },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/auto-test/scenarios')
      const allList = Array.isArray(data) ? data : (data?.items || data?.scenarios || [])
      this.setData({ allList })
      this.filterList()
    } catch (err) {
      this.setData({ allList: [], list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  filterList() {
    const { allList, keyword } = this.data
    let list = allList
    if (keyword) {
      const kw = keyword.toLowerCase()
      list = allList.filter(item =>
        (item.name && item.name.toLowerCase().includes(kw)) ||
        (item.description && item.description.toLowerCase().includes(kw))
      )
    }
    this.setData({ list })
  },

  onSearch(e) {
    this.setData({ keyword: e.detail.value })
    this.filterList()
  },

  clearSearch() {
    this.setData({ keyword: '' })
    this.filterList()
  },

  async runScenario(e) {
    const id = e.currentTarget.dataset.id
    const name = e.currentTarget.dataset.name
    wx.showModal({
      title: '确认运行',
      content: `运行场景「${name}」？`,
      success: async (res) => {
        if (res.confirm) {
          showLoading('启动中...')
          try {
            await api.post(`/api/auto-test/scenarios/${id}/run`)
            showToast('已启动', 'success')
          } catch (err) {
            showToast(err.message || '启动失败')
          } finally {
            hideLoading()
          }
        }
      }
    })
  }
})
