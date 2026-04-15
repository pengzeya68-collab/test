<template>
  <div class="interview-my">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">我的面试</h1>
          <p class="page-subtitle">查看历史面试记录和成绩分析</p>
        </div>
        <el-button type="primary" @click="$router.push('/interview/simulate')">
          <el-icon><VideoPlay /></el-icon>
          开始新面试
        </el-button>
      </div>

      <div class="filter-bar">
        <el-tabs v-model="activeTab" @tab-change="fetchSessions">
          <el-tab-pane label="全部记录" name="all" />
          <el-tab-pane label="进行中" name="in_progress" />
          <el-tab-pane label="已完成" name="completed" />
        </el-tabs>
      </div>

      <div class="session-list">
        <div 
          class="session-card" 
          v-for="session in sessions" 
          :key="session.id"
          @click="viewSession(session)"
        >
          <div class="card-header">
            <div class="session-title">{{ session.title }}</div>
            <el-tag :type="session.status === 'completed' ? 'success' : 'warning'" size="small">
              {{ session.status === 'completed' ? '已完成' : '进行中' }}
            </el-tag>
          </div>
          
          <div class="card-body">
            <div class="session-info">
              <div class="info-item">
                <el-icon size="14"><Position /></el-icon>
                <span>{{ session.position }}</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><Rank /></el-icon>
                <span>{{ session.level }}</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><Tickets /></el-icon>
                <span>{{ session.interview_type }}</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><List /></el-icon>
                <span>{{ session.question_count }}题</span>
              </div>
            </div>
            
            <div class="score-section" v-if="session.status === 'completed' && session.user_score !== null">
              <div class="score-display">
                <span class="score-label">得分：</span>
                <span class="score-value" :class="getScoreClass(session.user_score)">
                  {{ session.user_score }} / {{ session.total_score }}
                </span>
                <el-tag
                  :type="session.user_score >= 60 ? 'success' : 'danger'"
                  size="small"
                  class="result-tag"
                >
                  {{ session.user_score >= 60 ? '通过' : '未通过' }}
                </el-tag>
              </div>
            </div>
            <div class="score-section" v-else-if="session.status === 'completed'">
              <div class="score-display">
                <span class="score-label">状态：</span>
                <span class="score-value">已完成，待评分</span>
              </div>
            </div>
            
            <div class="progress-section" v-else>
              <span>继续上次面试</span>
              <el-progress :percentage="50" :show-text="false" style="width: 120px;" />
            </div>
          </div>
          
          <div class="card-footer">
            <span class="time">{{ session.start_time }}</span>
            <el-button type="primary" size="small">
              {{ session.status === 'completed' ? '查看详情' : '继续面试' }}
            </el-button>
          </div>
        </div>
      </div>

      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="perPage"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="fetchSessions"
        />
      </div>

      <div class="empty-state" v-if="sessions.length === 0 && !loading">
        <el-empty description="暂无面试记录，快去开始第一次模拟面试吧~">
          <el-button type="primary" @click="$router.push('/interview/simulate')">
            开始面试
          </el-button>
        </el-empty>
      </div>

      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="6" animated />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  VideoPlay, Position, Rank, Tickets, List 
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const sessions = ref([])
const activeTab = ref('all')
const currentPage = ref(1)
const perPage = ref(10)
const total = ref(0)
const loading = ref(false)

onMounted(() => {
  fetchSessions()
})

const fetchSessions = async () => {
  loading.value = true
  try {
    // 构建fastapi_backend接口参数
    const params = {
      page: currentPage.value,
      size: perPage.value
    }

    // 状态筛选映射
    if (activeTab.value !== 'all') {
      if (activeTab.value === 'in_progress') {
        params.status_filter = 'started'  // 也可以考虑'submitted'
      } else if (activeTab.value === 'completed') {
        params.status_filter = 'finished'
      }
    }

    console.log('请求fastapi_backend参数:', params)
    const res = await request.get('/interview/sessions', { params })
    console.log('fastapi_backend接口返回:', res)

    // 检查响应结构
    if (res.data && res.data.items) {
      sessions.value = res.data.items.map(session => {
        let frontendStatus = 'in_progress'
        if (session.status === 'finished' || session.status === 'abandoned') {
          frontendStatus = 'completed'
        }

        const difficultyMap = { 'easy': '初级', 'medium': '中级', 'hard': '高级' }

        return {
          id: session.id,
          title: session.question_title || '模拟面试',
          position: '测试工程师',
          level: difficultyMap[session.question_difficulty] || '中级',
          interview_type: '技术面',
          status: frontendStatus,
          user_score: session.latest_score,
          total_score: 100,
          start_time: session.started_at ? formatDateTime(session.started_at) : formatDateTime(session.created_at),
          question_count: 1,
          raw_status: session.status,
        }
      })
      total.value = res.data.total || 0
    } else {
      // 如果响应结构不符合预期，使用原始数据
      console.warn('响应结构不符合预期，使用原始数据:', res)
      sessions.value = res.items || []
      total.value = res.total || 0
    }
  } catch (error) {
    console.error('获取面试记录失败:', error)
    ElMessage.error('获取面试记录失败: ' + (error.response?.data?.message || error.message))
    sessions.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 格式化日期时间
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
      second: '2-digit'
    }).replace(/\//g, '-')
  } catch (e) {
    console.error('日期格式化错误:', e)
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
  if (session.raw_status === 'started' || session.raw_status === 'submitted') {
    router.push(`/interview/simulate?session_id=${session.id}`)
  } else {
    router.push(`/interview/simulate?session_id=${session.id}`)
  }
}
</script>

<style scoped>
.interview-my {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: #09090B;
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.filter-bar {
  background: var(--tm-card-bg);
  border-radius: 12px 12px 0 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

:deep(.el-tabs__header) {
  margin: 0 20px;
}

.session-list {
  background: var(--tm-card-bg);
  border-radius: 0 0 12px 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 0 20px 20px 20px;
}

.session-card {
  padding: 24px 0;
  border-bottom: 1px solid var(--tm-border-light);
  cursor: pointer;
  transition: all 0.3s ease;
}

.session-card:hover {
  background: var(--tm-bg-hover);
  margin: 0 -20px;
  padding-left: 20px;
  padding-right: 20px;
  border-radius: 8px;
}

.session-card:last-child {
  border-bottom: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.session-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
  flex: 1;
  margin-right: 12px;
}

.session-info {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.score-section {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.score-value {
  font-size: 24px;
  font-weight: bold;
}

.score-value.excellent {
  color: #67c23a;
}

.score-value.good {
  color: #e6a23c;
}

.score-value.poor {
  color: #f56c6c;
}

.result-tag {
  margin-left: 12px;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 16px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--tm-border-light);
}

.time {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.empty-state, .loading-state {
  background: var(--tm-card-bg);
  padding: 60px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

@media (max-width: 768px) {
  .session-info {
    gap: 12px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
