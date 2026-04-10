<template>
  <div class="learning-path-detail">
    <div class="container">
      <!-- 加载状态 -->
      <div class="loading" v-if="loading">
        <el-spinner size="40" />
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
                开始学习
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
              v-for="exercise in path.exercises" 
              :key="exercise.id"
              @click="goToExercise(exercise.id)"
              shadow="hover"
            >
              <div class="exercise-header">
                <h3 class="exercise-title">{{ exercise.title }}</h3>
                <el-tag :type="getDifficultyTagType(exercise.difficulty)" size="small">
                  {{ getDifficultyText(exercise.difficulty) }}
                </el-tag>
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timer, Document, Calendar, List, PriceTag, Collection } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const path = ref(null)
const loading = ref(false)
const pathId = route.params.id
const isCollected = ref(false)

onMounted(() => {
  fetchPathDetail()
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
  // 如果有习题，跳转到第一个习题
  if (path.value?.exercises?.length > 0) {
    router.push(`/exercises/${path.value.exercises[0].id}`)
  } else {
    ElMessage.info('该路径暂无习题，请先选择其他路径')
  }
}

const toggleCollect = () => {
  isCollected.value = !isCollected.value
  ElMessage.success(isCollected.value ? '收藏成功' : '取消收藏成功')
  // 后续对接后端收藏接口
}
</script>

<style scoped>
.learning-path-detail {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
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
  background: white;
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
  color: #303133;
  margin-bottom: 16px;
  line-height: 1.4;
}

.path-desc {
  font-size: 16px;
  color: #606266;
  line-height: 1.8;
  margin-bottom: 30px;
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
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.path-actions {
  display: flex;
  gap: 16px;
}

.exercises-section {
  background: white;
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
  color: #303133;
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

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.exercise-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.exercise-desc {
  color: #606266;
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
  color: #909399;
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
}
</style>
