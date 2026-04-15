<template>
  <div class="learning-path-detail">
    <div class="container">
      <!-- 加载状态 -->
      <div class="loading" v-if="loading">
        <el-icon class="is-loading" size="40"><Loading /></el-icon>
      </div>

      <!-- 路径详情 -->
      <div v-if="!loading && path" class="path-content">
        <!-- 头部信息 -->
        <div class="path-header">
          <div class="path-basic">
            <div class="path-tags">
              <el-tag :type="getStageTagType(path.stage)" size="large">
                阶段{{ path.stage }}
              </el-tag>
              <el-tag :type="getDifficultyTagType(path.difficulty)" size="large">
                {{ getDifficultyText(path.difficulty) }}
              </el-tag>
              <el-tag type="info" size="large">
                {{ path.language }}
              </el-tag>
            </div>
            <h1 class="path-title">{{ path.title }}</h1>
            <p class="path-desc">{{ path.description }}</p>

            <!-- 学习进度 -->
            <div class="progress-section" v-if="isLoggedIn">
              <div class="progress-header">
                <span class="progress-label">学习进度</span>
                <span class="progress-stats">
                  已完成 {{ progressData.completed_exercises }}/{{ progressData.total_exercises }} 题
                </span>
                <span class="progress-percent">{{ progressData.progress_percent }}%</span>
              </div>
              <el-progress
                :percentage="progressData.progress_percent"
                :stroke-width="12"
                :color="progressColor"
                :format="() => ''"
              />
            </div>

            <!-- 完成庆祝 -->
            <div class="completion-banner" v-if="isLoggedIn && progressData.progress_percent >= 100">
              <div class="completion-icon">🎉</div>
              <div class="completion-text">
                <h3>恭喜完成本路径全部习题！</h3>
                <p>你已经掌握了这条学习路线的所有知识点，继续挑战下一个阶段吧！</p>
              </div>
              <el-button type="primary" @click="goToNextStage">
                下一阶段 →
              </el-button>
            </div>

            <div class="path-stats">
              <div class="stat-item">
                <el-icon size="20"><Timer /></el-icon>
                <span class="stat-value">{{ path.estimated_hours }}</span>
                <span class="stat-label">小时</span>
              </div>
              <div class="stat-item">
                <el-icon size="20"><Document /></el-icon>
                <span class="stat-value">{{ path.exercises.length }}</span>
                <span class="stat-label">个习题</span>
              </div>
              <div class="stat-item">
                <el-icon size="20"><Calendar /></el-icon>
                <span class="stat-value">{{ formatDate(path.created_at) }}</span>
                <span class="stat-label">更新时间</span>
              </div>
            </div>
            <div class="path-actions">
              <el-button type="primary" size="large" @click="startLearning">
                {{ progressData.completed_exercises > 0 ? '继续学习' : '开始学习' }}
              </el-button>
              <el-button size="large" @click="toggleCollect">
                {{ isCollected ? '取消收藏' : '加入收藏' }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 习题列表 -->
        <div class="exercises-section">
          <h2 class="section-title">
            <el-icon size="24"><List /></el-icon>
            本路径习题
          </h2>
          <div class="exercises-list">
            <el-card
              class="exercise-card"
              :class="{ 'exercise-completed': isExerciseCompleted(exercise.id) }"
              v-for="exercise in path.exercises"
              :key="exercise.id"
              @click="goToExercise(exercise.id)"
              shadow="hover"
            >
              <div class="exercise-header">
                <div class="exercise-title-row">
                  <span class="exercise-status-icon" v-if="isExerciseCompleted(exercise.id)">✅</span>
                  <span class="exercise-status-icon pending" v-else>⬜</span>
                  <h3 class="exercise-title">{{ exercise.title }}</h3>
                </div>
                <div class="exercise-badges">
                  <el-tag v-if="getExerciseScore(exercise.id)" type="success" size="small">
                    {{ getExerciseScore(exercise.id) }}分
                  </el-tag>
                  <el-tag :type="getDifficultyTagType(exercise.difficulty)" size="small">
                    {{ getDifficultyText(exercise.difficulty) }}
                  </el-tag>
                </div>
              </div>
              <p class="exercise-desc">{{ exercise.description }}</p>
              <div class="exercise-meta">
                <div class="meta-item">
                  <el-icon size="16"><Timer /></el-icon>
                  <span>{{ exercise.time_estimate }}分钟</span>
                </div>
                <div class="meta-item" v-if="exercise.knowledge_point">
                  <el-icon size="16"><PriceTag /></el-icon>
                  <span>{{ exercise.knowledge_point }}</span>
                </div>
                <div class="meta-item">
                  <el-icon size="16"><Collection /></el-icon>
                  <span>{{ exercise.category }}</span>
                </div>
                <div class="meta-item" v-if="getExerciseAttempts(exercise.id) > 0">
                  <el-icon size="16"><Edit /></el-icon>
                  <span>尝试 {{ getExerciseAttempts(exercise.id) }} 次</span>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 空状态 -->
          <div class="empty-state" v-if="path.exercises.length === 0">
            <el-empty description="该路径暂无习题" />
          </div>
        </div>
      </div>

      <!-- 不存在 -->
      <div class="empty-state" v-if="!loading && !path">
        <el-empty description="学习路径不存在" />
        <el-button type="primary" @click="goBack" style="margin-top: 20px;">
          返回列表
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timer, Document, Calendar, List, PriceTag, Collection, Edit, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)

const path = ref(null)
const loading = ref(false)
const pathId = route.params.id
const isCollected = ref(false)
const progressData = ref({
  total_exercises: 0,
  completed_exercises: 0,
  progress_percent: 0,
  exercises: [],
})

const progressColor = computed(() => {
  const p = progressData.value.progress_percent
  if (p >= 100) return '#67c23a'
  if (p >= 60) return '#409eff'
  if (p >= 30) return '#e6a23c'
  return '#909399'
})

onMounted(() => {
  fetchPathDetail()
  if (isLoggedIn.value) {
    fetchProgress()
  }
})

const fetchPathDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/learning-paths/${pathId}`)
    path.value = res
  } catch (error) {
    console.error('获取学习路径详情失败:', error)
    ElMessage.error('获取学习路径详情失败')
  } finally {
    loading.value = false
  }
}

const fetchProgress = async () => {
  try {
    const res = await request.get(`/learning-paths/${pathId}/progress`)
    progressData.value = res
  } catch (error) {
    console.error('获取学习进度失败:', error)
  }
}

const isExerciseCompleted = (exerciseId) => {
  const ex = progressData.value.exercises?.find(e => e.id === exerciseId)
  return ex?.completed || false
}

const getExerciseScore = (exerciseId) => {
  const ex = progressData.value.exercises?.find(e => e.id === exerciseId)
  return ex?.score
}

const getExerciseAttempts = (exerciseId) => {
  const ex = progressData.value.exercises?.find(e => e.id === exerciseId)
  return ex?.attempts || 0
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

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const goToExercise = (exerciseId) => {
  router.push(`/exercises/${exerciseId}`)
}

const goBack = () => {
  router.back()
}

const startLearning = () => {
  if (path.value?.exercises?.length > 0) {
    const nextExercise = progressData.value.exercises?.find(e => !e.completed)
    if (nextExercise) {
      router.push(`/exercises/${nextExercise.id}`)
    } else {
      router.push(`/exercises/${path.value.exercises[0].id}`)
    }
  } else {
    ElMessage.info('该路径暂无习题，请先选择其他路径')
  }
}

const goToNextStage = () => {
  const nextStage = (path.value?.stage || 0) + 1
  if (nextStage <= 5) {
    router.push({ path: '/learning-paths', query: { stage: nextStage } })
  } else {
    ElMessage.success('你已经完成了所有阶段的学习！')
    router.push('/skill-analysis')
  }
}

const toggleCollect = () => {
  isCollected.value = !isCollected.value
  ElMessage.success(isCollected.value ? '收藏成功' : '取消收藏成功')
}
</script>

<style scoped>
.learning-path-detail {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-elevated);
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.loading {
  text-align: center;
  padding: 100px 0;
}

.path-header {
  background: #18181B;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.path-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.path-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin-bottom: 16px;
  line-height: 1.4;
}

.path-desc {
  font-size: 16px;
  color: var(--tm-text-regular);
  line-height: 1.8;
  margin-bottom: 20px;
}

.progress-section {
  background: linear-gradient(135deg, #f0f5ff 0%, #e8f4f8 100%);
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 20px;
  border: 1px solid #d9ecff;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.progress-stats {
  font-size: 14px;
  color: var(--tm-text-regular);
}

.progress-percent {
  margin-left: auto;
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}

.completion-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px 28px;
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
  border-radius: 12px;
  border: 1px solid rgba(103, 194, 58, 0.2);
  margin-bottom: 20px;
}

.completion-icon {
  font-size: 48px;
  flex-shrink: 0;
}

.completion-text {
  flex: 1;
}

.completion-text h3 {
  font-size: 18px;
  font-weight: 700;
  color: #67c23a;
  margin: 0 0 6px;
}

.completion-text p {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
  line-height: 1.6;
}

.path-stats {
  display: flex;
  gap: 40px;
  margin-bottom: 30px;
  padding: 20px 0;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.path-actions {
  display: flex;
  gap: 16px;
}

.exercises-section {
  background: #18181B;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin-bottom: 30px;
}

.exercises-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.exercise-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.exercise-card:hover {
  transform: translateX(4px);
}

.exercise-card.exercise-completed {
  border-left: 3px solid #67c23a;
  background: rgba(103, 194, 58, 0.02);
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.exercise-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.exercise-status-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.exercise-status-icon.pending {
  opacity: 0.4;
}

.exercise-badges {
  display: flex;
  gap: 8px;
  align-items: center;
}

.exercise-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0;
}

.exercise-desc {
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.exercise-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

@media (max-width: 768px) {
  .path-header,
  .exercises-section {
    padding: 24px;
  }

  .path-title {
    font-size: 24px;
  }

  .path-stats {
    gap: 20px;
  }

  .stat-value {
    font-size: 20px;
  }

  .section-title {
    font-size: 20px;
  }

  .progress-header {
    flex-wrap: wrap;
    gap: 8px;
  }

  .progress-percent {
    margin-left: 0;
  }
}
</style>
