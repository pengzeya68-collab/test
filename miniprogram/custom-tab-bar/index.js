Component({
  data: {
    selected: 0
  },

  methods: {
    switchTab(e) {
      const url = e.currentTarget.dataset.url
      const index = e.currentTarget.dataset.index
      this.setData({ selected: index })
      wx.switchTab({ url })
    }
  }
})
