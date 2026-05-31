const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: { list: [], loading: false, noMore: false, page: 1, pageSize: 20 },

  onLoad() {},

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.setData({ page: 1, noMore: false })
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const data = await api.get('/api/v1/exercise/wrong-answers')
      const list = Array.isArray(data) ? data : (data?.items || data?.wrong_answers || [])
      this.setData({ list, noMore: list.length < this.data.pageSize })
    } catch (err) {
      this.setData({ list: [] })
      showToast('加载错题失败')
    } finally {
      this.setData({ loading: false })
    }
  },

  loadMore() {
    if (this.data.noMore || this.data.loading) return
    const nextPage = this.data.page + 1
    this.setData({ page: nextPage, loading: true })

    api.get('/api/v1/exercise/wrong-answers', { page: nextPage, page_size: this.data.pageSize })
      .then(data => {
        const moreList = Array.isArray(data) ? data : (data?.items || data?.wrong_answers || [])
        this.setData({
          list: [...this.data.list, ...moreList],
          noMore: moreList.length < this.data.pageSize,
          loading: false
        })
      })
      .catch(() => {
        this.setData({ loading: false })
        showToast('加载更多失败')
      })
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  }
})
