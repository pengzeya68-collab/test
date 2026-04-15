<template>
  <div class="learning-paths">
    <div class="container">
      <!-- 顶部筛选 -->
      <div class="filter-bar">
        <h1 class="page-title">学习路径</h1>
        <div class="filters">
          <el-radio-group v-model="currentStage" @change="handleStageChange">
            <el-radio-button :value="1">阶段1</el-radio-button>
            <el-radio-button :value="2">阶段2</el-radio-button>
            <el-radio-button :value="3">阶段3</el-radio-button>
            <el-radio-button :value="4">阶段4</el-radio-button>
            <el-radio-button :value="5">阶段5</el-radio-button>
          </el-radio-group>
          <el-select
            v-model="currentDifficulty"
            placeholder="难度筛选"
            @change="fetchLearningPaths"
            style="width: 120px; margin-left: 20px;"
          >
            <el-option label="全部" value="" />
            <el-option label="初级" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </div>
      </div>

      <!-- 阶段说明 -->
      <div class="stage-info" v-if="currentStage > 0">
        <el-alert
          :title="stageInfo.title"
          :description="stageInfo.description"
          type="info"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 学习路径列表 -->
      <div class="paths-grid">
        <div
          class="path-card"
          v-for="path in learningPaths"
          :key="path.id"
        >
          <div class="path-header">
            <el-tag :type="getStageTagType(path.stage)" size="small">
              阶段{{ path.stage }}
            </el-tag>
            <el-tag :type="getDifficultyTagType(path.difficulty)" size="small">
              {{ getDifficultyText(path.difficulty) }}
            </el-tag>
          </div>
          <h3 class="path-title">{{ path.title }}</h3>
          <p class="path-desc">{{ path.description }}</p>

          <!-- 进度条 -->
          <div class="path-progress" v-if="isLoggedIn && getPathProgress(path.id)">
            <div class="progress-info">
              <span class="progress-text">已完成 {{ getPathProgress(path.id).completed_exercises }}/{{ getPathProgress(path.id).total_exercises }} 题</span>
              <span class="progress-percent">{{ getPathProgress(path.id).progress_percent }}%</span>
            </div>
            <el-progress
              :percentage="getPathProgress(path.id).progress_percent"
              :stroke-width="6"
              :show-text="false"
              :color="getPathProgressColor(path.id)"
            />
          </div>

          <div class="path-meta">
            <div class="meta-item">
              <el-icon size="16"><Timer /></el-icon>
              <span>{{ path.estimated_hours }}小时</span>
            </div>
            <div class="meta-item">
              <el-icon size="16"><Document /></el-icon>
              <span>{{ path.exercise_count }}个习题</span>
            </div>
            <div class="meta-item">
              <el-icon size="16"><Collection /></el-icon>
              <span>{{ path.language }}</span>
            </div>
          </div>
          <div class="path-footer">
            <el-button type="primary" size="small" plain @click.stop="goToDetail(path.id)">
              {{ getPathProgress(path.id)?.completed_exercises > 0 ? '继续学习' : '开始学习' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-if="learningPaths.length === 0 && !loading">
        <el-empty description="该阶段暂无学习路径" />
      </div>

      <!-- 加载状态 -->
      <div class="loading" v-if="loading">
        <el-icon class="is-loading" size="40"><Loading /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timer, Document, Collection, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)

const learningPaths = ref([])
const loading = ref(false)
const currentStage = ref(1)
const currentDifficulty = ref('')
const allProgress = ref([])

const stageInfos = {
  1: {
    title: '阶段1 - 测试入门筑基',
    description: '适合零基础入门，掌握软件测试基础理论、测试方法、计算机基础和SQL，为测试生涯打好基础。预计4周完成。'
  },
  2: {
    title: '阶段2 - 功能测试精通',
    description: '精通Web/APP/小程序等各类项目的功能测试，掌握完整的测试流程，能独立负责项目测试。预计8周完成。'
  },
  3: {
    title: '阶段3 - 测试技术进阶',
    description: '掌握接口测试、Linux、数据库进阶、性能测试基础，成为中级测试工程师。预计12周完成。'
  },
  4: {
    title: '阶段4 - 自动化测试专家',
    description: '精通Python编程、接口自动化、UI自动化、APP自动化、性能测试，成为高级自动化测试工程师。预计16周完成。'
  },
  5: {
    title: '阶段5 - 测试架构师之路',
    description: '掌握测试平台开发、DevOps、质量体系建设、专项测试技术，向测试架构师/测试专家方向发展。预计20周以上。'
  }
}

const stageInfo = computed(() => {
  return stageInfos[currentStage.value] || {}
})

onMounted(() => {
  if (route.query.stage) {
    currentStage.value = parseInt(route.query.stage)
  }
  fetchLearningPaths()
  if (isLoggedIn.value) {
    fetchAllProgress()
  }
})

const fetchLearningPaths = async () => {
  loading.value = true
  try {
    const params = {}
    if (currentStage.value > 0) {
      params.stage = currentStage.value
    }
    if (currentDifficulty.value) {
      params.difficulty = currentDifficulty.value
    }

    const res = await request.get('/learning-paths', { params })
    learningPaths.value = res
  } catch (error) {
    console.error('获取学习路径失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchAllProgress = async () => {
  try {
    const res = await request.get('/learning-paths/all-progress')
    allProgress.value = res.progress || []
  } catch (error) {
    console.error('获取学习进度失败:', error)
  }
}

const getPathProgress = (pathId) => {
  return allProgress.value.find(p => p.path_id === pathId)
}

const getPathProgressColor = (pathId) => {
  const p = getPathProgress(pathId)
  if (!p) return '#909399'
  if (p.progress_percent >= 100) return '#67c23a'
  if (p.progress_percent >= 60) return '#409eff'
  if (p.progress_percent >= 30) return '#e6a23c'
  return '#909399'
}

const handleStageChange = () => {
  fetchLearningPaths()
}

const getStageTagType = (stage) => {
  const types = ['', 'primary', 'success', 'warning', 'danger', 'info']
  return types[stage] || 'info'
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return map[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const map = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return map[difficulty] || difficulty
}

const goToDetail = (id) => {
  router.push(`/learning-paths/${id}`)
}
</script>

<style scoped>
.learning-paths {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-page);
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 20px;
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  padding: 24px;
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.stage-info {
  margin-bottom: 32px;
}

.paths-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  position: relative;
}

.path-card {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 16px;
  padding: 28px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
}

.path-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.path-header {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.path-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin-bottom: 12px;
  line-height: 1.4;
}

.path-desc {
  color: var(--tm-text-secondary);
  line-height: 1.7;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  font-size: 14px;
}

.path-progress {
  margin-bottom: 16px;
  padding: 14px 16px;
  background: rgba(214, 51, 108, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(214, 51, 108, 0.08);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.progress-text {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.progress-percent {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-color-primary);
}

.path-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--tm-border-light);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.path-footer {
  display: flex;
  justify-content: flex-end;
}

.empty-state {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  padding: 80px 20px;
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  text-align: center;
}

.loading {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  padding: 80px 20px;
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  text-align: center;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-title {
    font-size: 24px;
  }

  .paths-grid {
    grid-template-columns: 1fr;
  }
}
</style>
