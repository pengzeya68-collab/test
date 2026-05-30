const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: {
    allList: [],
    list: [],
    groups: [],
    keyword: '',
    activeGroup: '',
    loading: false
  },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.loadGroups()
    this.loadData()
  },

  async loadGroups() {
    try {
      const data = await api.get('/api/auto-test/groups/tree')
      const groups = Array.isArray(data) ? data : (data?.items || [])
      this.setData({ groups })
    } catch (err) { }
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/auto-test/cases')
      const allList = Array.isArray(data) ? data : (data?.items || data?.cases || [])
      this.setData({ allList })
      this.filterList()
    } catch (err) {
      this.setData({ allList: [], list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  filterList() {
    const { allList, keyword, activeGroup } = this.data
    let list = allList
    if (activeGroup) {
      list = list.filter(item =>
        item.group_id === activeGroup || item.group_name === activeGroup
      )
    }
    if (keyword) {
      const kw = keyword.toLowerCase()
      list = list.filter(item =>
        (item.name && item.name.toLowerCase().includes(kw)) ||
        (item.url && item.url.toLowerCase().includes(kw)) ||
        (item.path && item.path.toLowerCase().includes(kw))
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

  selectGroup(e) {
    this.setData({ activeGroup: e.currentTarget.dataset.val })
    this.filterList()
  },

  async runCase(e) {
    const id = e.currentTarget.dataset.id
    const name = e.currentTarget.dataset.name
    wx.showModal({
      title: '快速运行',
      content: `运行用例「${name}」？`,
      success: async (res) => {
        if (res.confirm) {
          showLoading('运行中...')
          try {
            await api.post(`/api/auto-test/cases/${id}/quick-run`)
            showToast('已启动', 'success')
          } catch (err) {
            showToast(err.message || '运行失败')
          } finally {
            hideLoading()
          }
        }
      }
    })
  }
})
