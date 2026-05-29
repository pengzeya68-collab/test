const api = require('../../utils/api')
const { getDifficultyTag, debounce } = require('../../utils/util')

Page({
  data: {
    exercises: [],
    keyword: '',
    filter: {
      category: '',
      categoryName: '分类',
      difficulty: '',
      difficultyName: '难度',
      status: '',
      statusName: '状态'
    },
    page: 1,
    pageSize: 20,
    hasMore: true,
    loading: false,
    categories: []
  },

  onLoad() {
    this.loadCategories()
    this.loadExercises()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, exercises: [], hasMore: true })
    this.loadExercises()
    wx.stopPullDownRefresh()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  onSearch: debounce(function (e) {
    this.setData({ keyword: e.detail.value, page: 1, exercises: [], hasMore: true })
    this.loadExercises()
  }, 500),

  doSearch() {
    this.setData({ page: 1, exercises: [], hasMore: true })
    this.loadExercises()
  },

  async loadCategories() {
    try {
      const res = await api.get('/exercises/categories')
      const cats = res.categories || res || {}
      this.setData({ categories: Object.keys(cats).map(k => ({ name: k })) })
    } catch (err) {
      console.error('获取分类失败', err)
    }
  },

  async loadExercises() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const { keyword, filter, page, pageSize } = this.data
      const params = { page, page_size: pageSize }
      if (keyword) params.search = keyword
      if (filter.category) params.category = filter.category
      if (filter.difficulty) params.difficulty = filter.difficulty

      const res = await api.get('/exercises', params)
      const items = Array.isArray(res) ? res : (res.items || res || [])
      const exercises = items.map(item => ({
        ...item,
        difficultyTag: getDifficultyTag(item.difficulty)
      }))

      this.setData({
        exercises: this.data.exercises.concat(exercises),
        hasMore: items.length >= pageSize,
        loading: false
      })
    } catch (err) {
      console.error('获取习题失败', err)
      this.setData({ loading: false })
    }
  },

  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadExercises()
  },

  showCategoryPicker() {
    const cats = this.data.categories.map(c => c.name || c)
    cats.unshift('全部')
    wx.showActionSheet({
      itemList: cats,
      success: (res) => {
        const selected = cats[res.tapIndex]
        this.setData({
          'filter.category': selected === '全部' ? '' : selected,
          'filter.categoryName': selected === '全部' ? '分类' : selected,
          page: 1, exercises: [], hasMore: true
        })
        this.loadExercises()
      }
    })
  },

  showDifficultyPicker() {
    wx.showActionSheet({
      itemList: ['全部', '简单', '中等', '困难'],
      success: (res) => {
        const map = ['', 'easy', 'medium', 'hard']
        const nameMap = ['难度', '简单', '中等', '困难']
        this.setData({
          'filter.difficulty': map[res.tapIndex],
          'filter.difficultyName': nameMap[res.tapIndex],
          page: 1, exercises: [], hasMore: true
        })
        this.loadExercises()
      }
    })
  },

  showStatusPicker() {
    wx.showActionSheet({
      itemList: ['全部', '已完成', '未完成', '错题'],
      success: (res) => {
        const map = ['', 'completed', 'incomplete', 'wrong']
        const nameMap = ['状态', '已完成', '未完成', '错题']
        this.setData({
          'filter.status': map[res.tapIndex],
          'filter.statusName': nameMap[res.tapIndex],
          page: 1, exercises: [], hasMore: true
        })
        this.loadExercises()
      }
    })
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/exercise/detail?id=${id}` })
  }
})
