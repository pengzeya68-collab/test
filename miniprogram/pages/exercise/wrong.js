const api = require('../../utils/api')
const { getDifficultyTag } = require('../../utils/util')

Page({
  data: {
    wrongAnswers: [],
    page: 1,
    hasMore: true,
    loading: false
  },

  onLoad() { this.loadWrongAnswers() },

  onPullDownRefresh() {
    this.setData({ page: 1, wrongAnswers: [], hasMore: true })
    this.loadWrongAnswers()
    wx.stopPullDownRefresh()
  },

  async loadWrongAnswers() {
    if (this.data.loading) return
    this.setData({ loading: true })
    try {
      const res = await api.get('/exercise/wrong-answers')
      const wrongList = res.wrong_answers || []
      const items = wrongList.map(item => ({
        ...item,
        difficultyTag: getDifficultyTag(item.difficulty)
      }))
      this.setData({
        wrongAnswers: this.data.wrongAnswers.concat(items),
        hasMore: false,
        loading: false
      })
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadWrongAnswers()
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  }
})
