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
            
            <div class="score-section" v-if="session.status === 'completed'">
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
  // 先用静态数据测试
  sessions.value = [
    {
      id: 1,
      title: '中级测试工程师技术面试',
      position: '测试工程师',
      level: '中级',
      interview_type: '技术面',
      status: 'completed',
      user_score: 85,
      total_score: 100,
      start_time: '2026-03-14 20:00:00',
      question_count: 10
    },
    {
      id: 2,
      title: '自动化测试工程师面试',
      position: '自动化测试工程师',
      level: '高级',
      interview_type: '技术面',
      status: 'in_progress',
      user_score: null,
      total_score: 100,
      start_time: '2026-03-14 21:30:00',
      question_count: 15
    }
  ]
  total.value = 2
  loading.value = false
  // fetchSessions()
})

const fetchSessions = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: perPage.value,
      status: activeTab.value === 'all' ? '' : activeTab.value
    }
    
    console.log('请求参数:', params)
    const res = await request.get('/interview/sessions', { params })
    console.log('接口返回:', res)
    sessions.value = res.list || []
    total.value = res.total || 0
  } catch (error) {
    console.error('获取面试记录失败:', error)
    ElMessage.error('获取面试记录失败: ' + error.message)
    sessions.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const getScoreClass = (score) => {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  return 'poor'
}

const viewSession = (session) => {
  if (session.status === 'in_progress') {
    // 进行中的面试跳转到面试页面
    router.push(`/interview/simulate?session_id=${session.id}`)
  } else {
    // 已完成的跳转到详情页
    router.push(`/interview/detail/${session.id}`)
  }
}
</script>

<style scoped>
.interview-my {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
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
