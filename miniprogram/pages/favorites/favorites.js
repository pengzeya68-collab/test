const api = require('../../utils/api')
const { timeAgo } = require('../../utils/util')

Page({
  data: { favorites: [], activeTab: 'post', loading: false },

  onLoad() { this.loadFavorites() },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
    this.loadFavorites()
  },

  async loadFavorites() {
    this.setData({ loading: true })
    try {
      const typeMap = { post: 'post', exercise: 'exercise', note: 'note' }
      const res = await api.get('/favorites', { type: typeMap[this.data.activeTab] || '' })
      const favorites = (res.items || res || []).map(f => ({
        ...f,
        time: timeAgo(f.created_at)
      }))
      this.setData({ favorites, loading: false })
    } catch (err) {
      this.setData({ loading: false })
    }
  }
})
