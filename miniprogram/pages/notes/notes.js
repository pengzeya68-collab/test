const api = require('../../utils/api')
const auth = require('../../utils/auth')
const { showToast, showLoading, hideLoading } = require('../../utils/util')

Page({
  data: { list: [], loading: false, showModal: false, editingNote: null, noteTitle: '', noteContent: '', saving: false },

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
      const data = await api.get('/api/v1/notes/')
      const list = Array.isArray(data) ? data : (data?.items || [])
      this.setData({ list })
    } catch (err) {
      this.setData({ list: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  addNote() { this.setData({ showModal: true, editingNote: null, noteTitle: '', noteContent: '' }) },

  editNote(e) {
    const note = this.data.list[e.currentTarget.dataset.index]
    this.setData({ showModal: true, editingNote: note, noteTitle: note.title || '', noteContent: note.content || '' })
  },

  closeModal() { this.setData({ showModal: false }) },
  onTitleInput(e) { this.setData({ noteTitle: e.detail.value }) },
  onContentInput(e) { this.setData({ noteContent: e.detail.value }) },

  async saveNote() {
    const { noteTitle, noteContent, editingNote } = this.data
    if (!noteTitle.trim() || !noteContent.trim()) { showToast('请输入标题和内容'); return }
    this.setData({ saving: true })
    try {
      if (editingNote) {
        await api.put(`/api/v1/notes/${editingNote.id}`, { title: noteTitle, content: noteContent })
      } else {
        await api.post('/api/v1/notes/', { title: noteTitle, content: noteContent })
      }
      showToast('保存成功', 'success')
      this.closeModal()
      this.loadData()
    } catch (err) {
      showToast(err.message || '保存失败')
    } finally {
      this.setData({ saving: false })
    }
  },

  deleteNote(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除', content: '确定要删除这条笔记吗？',
      success: async (res) => {
        if (res.confirm) {
          try { await api.del(`/api/v1/notes/${id}`); showToast('已删除'); this.loadData() } catch (err) { showToast('删除失败') }
        }
      }
    })
  }
})
