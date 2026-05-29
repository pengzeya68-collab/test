function formatTime(date) {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = padZero(d.getMonth() + 1)
  const day = padZero(d.getDate())
  const hour = padZero(d.getHours())
  const minute = padZero(d.getMinutes())
  return `${year}-${month}-${day} ${hour}:${minute}`
}

function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = padZero(d.getMonth() + 1)
  const day = padZero(d.getDate())
  return `${year}-${month}-${day}`
}

function padZero(n) {
  return n < 10 ? '0' + n : '' + n
}

function timeAgo(date) {
  if (!date) return ''
  const now = Date.now()
  const diff = now - new Date(date).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return '刚刚'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months}个月前`
  return `${Math.floor(months / 12)}年前`
}

function getDifficultyTag(difficulty) {
  const map = {
    easy: { text: '简单', cls: 'tag-easy' },
    medium: { text: '中等', cls: 'tag-medium' },
    hard: { text: '困难', cls: 'tag-hard' },
    1: { text: '简单', cls: 'tag-easy' },
    2: { text: '中等', cls: 'tag-medium' },
    3: { text: '困难', cls: 'tag-hard' }
  }
  return map[difficulty] || { text: '未知', cls: 'tag-pending' }
}

function getStatusTag(status) {
  const map = {
    success: { text: '通过', cls: 'tag-pass' },
    passed: { text: '通过', cls: 'tag-pass' },
    fail: { text: '失败', cls: 'tag-fail' },
    failed: { text: '失败', cls: 'tag-fail' },
    error: { text: '错误', cls: 'tag-fail' },
    running: { text: '运行中', cls: 'tag-running' },
    pending: { text: '等待中', cls: 'tag-pending' },
    PENDING: { text: '等待中', cls: 'tag-pending' },
    PROGRESS: { text: '执行中', cls: 'tag-running' },
    SUCCESS: { text: '成功', cls: 'tag-pass' },
    FAILURE: { text: '失败', cls: 'tag-fail' },
    REVOKED: { text: '已取消', cls: 'tag-pending' }
  }
  return map[status] || { text: status || '未知', cls: 'tag-pending' }
}

function truncate(str, len = 50) {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}

function debounce(fn, delay = 500) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}

module.exports = {
  formatTime,
  formatDate,
  timeAgo,
  getDifficultyTag,
  getStatusTag,
  truncate,
  debounce,
  padZero
}
