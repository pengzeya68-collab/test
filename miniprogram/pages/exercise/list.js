const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast } = require('../../utils/util')

Page({
  data: {
    keyword: '',
    activeCategory: '',
    activeDifficulty: '',
    activeType: '',
    categories: [],
    exercises: [],
    loading: false,
    noMore: false,
    page: 1,
    pageSize: 20
  },

  onLoad() {},

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 })
    }
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    if (this.data.categories.length === 0) {
      this.loadCategories()
    }
    this.setData({ page: 1, exercises: [], noMore: false })
    this.loadExercises()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, exercises: [], noMore: false })
    this.loadExercises().then(() => wx.stopPullDownRefresh())
  },

  async loadCategories() {
    try {
      const data = await api.get('/api/v1/exercises/categories')
      const categories = []
      if (data && typeof data === 'object') {
        for (const [name, items] of Object.entries(data)) {
          categories.push({ name, count: Array.isArray(items) ? items.length : 0 })
        }
      }
      this.setData({ categories })
    } catch (err) {
      console.error('加载分类失败:', err.message)
    }
  },

  async loadExercises() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const params = []
      if (this.data.activeCategory) params.push(`category=${encodeURIComponent(this.data.activeCategory)}`)
      if (this.data.activeDifficulty) params.push(`difficulty=${this.data.activeDifficulty}`)
      if (this.data.activeType) params.push(`exercise_type=${encodeURIComponent(this.data.activeType)}`)
      if (this.data.keyword && this.data.keyword.trim()) params.push(`search=${encodeURIComponent(this.data.keyword.trim())}`)
      const query = params.length ? `?${params.join('&')}` : ''

      const data = await api.get(`/api/v1/exercises${query}`)
      const list = Array.isArray(data) ? data : (data?.items || [])
      this.setData({
        exercises: list,
        noMore: list.length < this.data.pageSize
      })
    } catch (err) {
      showToast('加载练习题失败')
    } finally {
      this.setData({ loading: false })
    }
  },

  loadMore() {
    if (this.data.noMore || this.data.loading) return
    const nextPage = this.data.page + 1
    this.setData({ page: nextPage, loading: true })

    const params = []
    if (this.data.activeCategory) params.push(`category=${encodeURIComponent(this.data.activeCategory)}`)
    if (this.data.activeDifficulty) params.push(`difficulty=${this.data.activeDifficulty}`)
    if (this.data.activeType) params.push(`exercise_type=${encodeURIComponent(this.data.activeType)}`)
    if (this.data.keyword && this.data.keyword.trim()) params.push(`search=${encodeURIComponent(this.data.keyword.trim())}`)
    params.push(`page=${nextPage}`)
    params.push(`page_size=${this.data.pageSize}`)
    const query = params.length ? `?${params.join('&')}` : ''

    api.get(`/api/v1/exercises${query}`).then(data => {
      const list = Array.isArray(data) ? data : (data?.items || [])
      this.setData({
        exercises: [...this.data.exercises, ...list],
        noMore: list.length < this.data.pageSize,
        loading: false
      })
    }).catch(() => {
      this.setData({ loading: false })
      showToast('加载更多失败')
    })
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  doSearch() {
    this.setData({ page: 1, exercises: [], noMore: false })
    this.loadExercises()
  },

  selectCategory(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.val, page: 1, exercises: [], noMore: false })
    this.loadExercises()
  },

  selectDifficulty(e) {
    this.setData({ activeDifficulty: e.currentTarget.dataset.val, page: 1, exercises: [], noMore: false })
    this.loadExercises()
  },

  selectType(e) {
    this.setData({ activeType: e.currentTarget.dataset.val, page: 1, exercises: [], noMore: false })
    this.loadExercises()
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  }
})
