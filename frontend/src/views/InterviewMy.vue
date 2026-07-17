<template>
  <div class="my-interviews-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">鎴戠殑闈㈣瘯</h1>
        <p class="page-desc">鏌ョ湅鍘嗗彶闈㈣瘯璁板綍鍜屾垚缁╁垎鏋</p>
      </div>
      <button class="btn-primary" @click="$router.push('/interview/simulate')">+ 寮€濮嬫柊闈㈣瘯</button>
    </header>

    <div class="tabs-container">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'all' }"
        @click="activeTab = 'all'; fetchSessions(true)"
      >鍏ㄩ儴璁板綍</div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'in_progress' }"
        @click="activeTab = 'in_progress'; fetchSessions(true)"
      >杩涜涓</div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'completed' }"
        @click="activeTab = 'completed'; fetchSessions(true)"
      >宸插畬鎴</div>
    </div>

    <div class="content-area" v-if="loading">
      <div class="loading-skeleton">
        <div class="sk-line" v-for="i in 6" :key="i"></div>
      </div>
    </div>

    <div class="content-area" v-else-if="sessions.length === 0">
      <div class="empty-content">
        <div class="empty-icon">馃摝</div>
        <p class="empty-text">鏆傛棤闈㈣瘯璁板綍锛屽揩鍘诲紑濮嬬涓€娆℃ā鎷熼潰璇曞惂~</p>
        <button class="btn-primary" @click="$router.push('/interview/simulate')">寮€濮嬮潰璇</button>
      </div>
    </div>

    <div class="content-area session-area" v-else>
      <div class="session-list">
        <div
          class="session-card"
          v-for="session in sessions"
          :key="session.id"
          @click="viewSession(session)"
        >
          <div class="card-header">
            <span class="session-title">{{ session.title }}</span>
            <span class="status-tag" :class="session.status === 'completed' ? 'done' : (session.status === 'abandoned' ? 'abandoned' : 'ongoing')">
              {{ session.status === 'completed' ? '已完成' : (session.status === 'abandoned' ? '已放弃' : '进行中') }}
            </span>
          </div>

          <div class="card-body">
            <div class="session-meta">
              <span class="meta-item">馃搷 {{ session.position }}</span>
              <span class="meta-item">馃搳 {{ session.level }}</span>
              <span class="meta-item">馃帿 {{ session.interview_type }}</span>
              <span class="meta-item">馃摑 {{ session.question_count }}棰</span>
            </div>

            <div class="score-row" v-if="session.status === 'completed' && session.user_score !== null">
              <span class="score-label">寰楀垎锛</span>
              <span class="score-value" :class="getScoreClass(session.user_score)">
                {{ session.user_score }} / {{ session.total_score }}
              </span>
              <span class="result-badge" :class="session.user_score >= 60 ? 'pass' : 'fail'">
                {{ session.user_score >= 60 ? '閫氳繃' : '鏈€氳繃' }}
              </span>
            </div>
            <div class="score-row" v-else-if="session.status === 'completed'">
              <span class="score-label">鐘舵€侊細</span>
              <span class="score-value pending">宸插畬鎴愶紝寰呰瘎鍒</span>
            </div>

            <div class="progress-row" v-else>
              <span>缁х画涓婃闈㈣瘯</span>
              <div class="mini-progress-bar">
                <div class="mini-progress-fill" :style="{ width: (session.question_count > 0 ? Math.min((session.answered_count || 0) / session.question_count * 100, 100) : 0) + '%' }"></div>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <span class="footer-time">{{ session.start_time }}</span>
            <button class="btn-sm">
              {{ session.status === 'completed' ? '鏌ョ湅璇︽儏' : '缁х画闈㈣瘯' }}
            </button>
          </div>
        </div>
      </div>

      <div class="pagination-bar" v-if="total > 0">
        <button
          class="page-btn"
          :disabled="currentPage <= 1"
          @click="currentPage--; fetchSessions()"
        >涓婁竴椤</button>
        <span class="page-info">绗?{{ currentPage }} 椤?/ 鍏?{{ Math.ceil(total / perPage) }} 椤碉紙{{ total }} 鏉★級</span>
        <button
          class="page-btn"
          :disabled="currentPage >= Math.ceil(total / perPage)"
          @click="currentPage++; fetchSessions()"
        >涓嬩竴椤</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()

const sessions = ref([])
const activeTab = ref('all')
const currentPage = ref(1)
const perPage = ref(10)
const total = ref(0)
const loading = ref(false)

onMounted(() => {
  fetchSessions(true)
})

const fetchSessions = async (resetPage = false) => {
  if (resetPage) currentPage.value = 1
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: perPage.value,
    }

    if (activeTab.value !== 'all') {
      if (activeTab.value === 'in_progress') {
        params.status_filter = 'started'
      } else if (activeTab.value === 'completed') {
        params.status_filter = 'finished'
      }
    }

    const res = await request.get('/interview/sessions', { params })

    if (res.data && res.data.items) {
      sessions.value = res.data.items.map(session => {
        let frontendStatus = 'in_progress'
        if (session.status === 'finished') {
          frontendStatus = 'completed'
        } else if (session.status === 'abandoned') {
          frontendStatus = 'abandoned'
        }

        const difficultyMap = { easy: '初级', medium: '中级', hard: '高级' }

        return {
          id: session.id,
          title: session.title || session.question_title || '模拟面试',
          position: session.position || '测试工程师',
          level: session.level || difficultyMap[session.question_difficulty] || '中级',
          interview_type: session.interview_type || '技术面',
          status: frontendStatus,
          user_score: session.latest_score,
          total_score: 100,
          start_time: session.started_at ? formatDateTime(session.started_at) : formatDateTime(session.created_at),
          question_count: session.question_count || 1,
          answered_count: session.answered_count || 0,
          raw_status: session.status,
        }
      })
      total.value = res.data.total || 0
    } else {
      sessions.value = res.items || []
      total.value = res.total || 0
    }
  } catch (error) {
    console.error('鑾峰彇闈㈣瘯璁板綍澶辫触:', error)
    ElMessage.error('鑾峰彇闈㈣瘯璁板綍澶辫触: ' + (error.response?.data?.message || error.message))
    sessions.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  try {
    const date = new Date(dateTimeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).replace(/\//g, '-')
  } catch {
    return dateTimeStr
  }
}

const getScoreClass = (score) => {
  if (score === null || score === undefined) return 'poor'
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  return 'poor'
}

const viewSession = (session) => {
  if (session.status === 'completed') {
    router.push(`/interview/detail/${session.id}`)
  } else {
    router.push(`/interview/simulate?session_id=${session.id}`)
  }
}
</script>

<style scoped>
.my-interviews-page {
  width: 100%;
  min-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  padding: 40px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  flex-shrink: 0;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.page-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
}

.btn-primary {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  border: none;
  padding: 11px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(var(--tm-color-primary-rgb), 0.3);
  transition: all 0.3s ease;
  white-space: nowrap;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--tm-color-primary-rgb), 0.45);
}

/* Tabs */
.tabs-container {
  display: flex;
  gap: 28px;
  border-bottom: 1px solid #27272a;
  margin-bottom: 32px;
  flex-shrink: 0;
}

.tab-item {
  padding: 12px 0;
  color: var(--tm-text-regular);
  cursor: pointer;
  position: relative;
  font-size: 15px;
  font-weight: 500;
  transition: color 0.2s;
}
.tab-item:hover { color: var(--tm-color-primary); }
.tab-item.active {
  color: var(--tm-color-primary);
  font-weight: 600;
}
.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--tm-color-primary);
  border-radius: 1px;
}

/* Content Area */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 14px;
}

.session-area {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  padding: 20px 24px;
}

/* Loading */
.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 40px;
}
.sk-line {
  height: 18px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.04);
  animation: skPulse 1.6s ease-in-out infinite;
}
@keyframes skPulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

/* Empty */
.content-area:has(.empty-content) {
  justify-content: center;
  align-items: center;
  background: var(--tm-card-bg);
  border: 1px dashed var(--tm-border-light);
}
.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 0;
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 8px;
}
.empty-text {
  color: var(--tm-text-regular);
  font-size: 14px;
  margin: 0 0 8px;
}

/* Session List */
.session-list {
  display: flex;
  flex-direction: column;
}
.session-card {
  padding: 20px 16px;
  border-bottom: 1px solid var(--tm-border-light);
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 10px;
}
.session-card:last-child { border-bottom: none; }
.session-card:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.session-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--tm-text-primary);
  flex: 1;
  margin-right: 12px;
}
.status-tag {
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.status-tag.ongoing { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
.status-tag.done { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.status-tag.abandoned { background: rgba(161, 161, 170, 0.12); color: #a1a1aa; }

.session-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.meta-item { font-size: 13px; color: var(--tm-text-regular); }

.score-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.score-label { font-size: 13px; color: var(--tm-text-secondary); }
.score-value {
  font-size: 22px;
  font-weight: 800;
}
.score-value.excellent { color: #34d399; }
.score-value.good { color: #fbbf24; }
.score-value.poor { color: #f87171; }
.score-value.pending { font-size: 14px; color: var(--tm-text-regular); font-weight: 500; }

.result-badge {
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.result-badge.pass { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.result-badge.fail { background: rgba(248, 113, 113, 0.12); color: #f87171; }

.progress-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-bottom: 14px;
}
.mini-progress-bar {
  width: 120px;
  height: 5px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}
.mini-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}
.footer-time { font-size: 12px; color: #52525b; }

.btn-sm {
  padding: 7px 18px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-sm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--tm-color-primary-rgb), 0.3);
}

/* Pagination */
.pagination-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--tm-border-light);
}
.page-btn {
  padding: 7px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--tm-border-light);
  border-radius: 6px;
  color: var(--tm-text-regular);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.page-btn:hover:not(:disabled) { border-color: var(--tm-color-primary); color: var(--tm-color-primary); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-info { font-size: 13px; color: var(--tm-text-secondary); }

@media (max-width: 768px) {
  .my-interviews-page { padding: 24px; }
  .page-header { flex-direction: column; align-items: flex-start; gap: 16px; }
  .session-meta { gap: 12px; }
}
</style>
