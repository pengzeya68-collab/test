function formatTime(date) {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getDifficultyTag(difficulty) {
  const map = {
    easy: { text: '简单', cls: 'tag-easy' },
    medium: { text: '中等', cls: 'tag-medium' },
    hard: { text: '困难', cls: 'tag-hard' }
  }
  return map[difficulty] || { text: difficulty || '未知', cls: 'tag-easy' }
}

function getModuleLabel(module) {
  const map = {
    normal: '常规练习',
    exam: '考试模拟',
    interview: '面试准备',
    project: '项目实战'
  }
  return map[module] || module || '常规练习'
}

function showToast(title, icon = 'none') {
  wx.showToast({ title, icon, duration: 2000 })
}

function showLoading(title = '加载中...') {
  wx.showLoading({ title, mask: true })
}

function hideLoading() {
  wx.hideLoading()
}

module.exports = {
  formatTime,
  formatDate,
  getDifficultyTag,
  getModuleLabel,
  showToast,
  showLoading,
  hideLoading
}
