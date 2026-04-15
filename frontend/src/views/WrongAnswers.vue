<template>
  <div class="wrong-answers-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">📖 错题本</h1>
        <p class="page-desc">回顾错题，查漏补缺，避免重复犯错</p>
      </div>

      <div class="stats-bar">
        <div class="stat-chip wrong">
          <span class="stat-num">{{ wrongData.wrong_count }}</span>
          <span class="stat-label">待复习</span>
        </div>
        <div class="stat-chip mastered">
          <span class="stat-num">{{ wrongData.mastered_count }}</span>
          <span class="stat-label">已掌握</span>
        </div>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="待复习" name="wrong">
          <div class="exercise-list" v-if="wrongData.wrong_answers.length > 0">
            <div
              v-for="item in wrongData.wrong_answers"
              :key="item.id"
              class="wrong-card"
              @click="goToExercise(item.id)"
            >
              <div class="wrong-card-left">
                <div class="wrong-icon">✗</div>
              </div>
              <div class="wrong-card-body">
                <div class="wrong-card-header">
                  <h3 class="wrong-title">{{ item.title }}</h3>
                  <div class="wrong-badges">
                    <el-tag type="danger" size="small">错 {{ item.wrong_count }} 次</el-tag>
                    <el-tag :type="getDifficultyType(item.difficulty)" size="small">
                      {{ getDifficultyText(item.difficulty) }}
                    </el-tag>
                  </div>
                </div>
                <div class="wrong-meta">
                  <span v-if="item.knowledge_point" class="meta-tag">
                    <el-icon size="14"><PriceTag /></el-icon>
                    {{ item.knowledge_point }}
                  </span>
                  <span v-if="item.category" class="meta-tag">
                    <el-icon size="14"><Collection /></el-icon>
                    {{ item.category }}
                  </span>
                  <span class="meta-tag">
                    <el-icon size="14"><Clock /></el-icon>
                    {{ item.last_wrong_at }}
                  </span>
                </div>
              </div>
              <div class="wrong-card-action">
                <el-button type="primary" size="small" plain>重做</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="没有错题，继续保持！" />
        </el-tab-pane>

        <el-tab-pane label="已掌握" name="mastered">
          <div class="exercise-list" v-if="wrongData.mastered.length > 0">
            <div
              v-for="item in wrongData.mastered"
              :key="item.id"
              class="wrong-card mastered-card"
              @click="goToExercise(item.id)"
            >
              <div class="wrong-card-left">
                <div class="mastered-icon">✓</div>
              </div>
              <div class="wrong-card-body">
                <div class="wrong-card-header">
                  <h3 class="wrong-title">{{ item.title }}</h3>
                  <el-tag type="success" size="small">已掌握</el-tag>
                </div>
                <div class="wrong-meta">
                  <span v-if="item.knowledge_point" class="meta-tag">
                    <el-icon size="14"><PriceTag /></el-icon>
                    {{ item.knowledge_point }}
                  </span>
                  <span v-if="item.category" class="meta-tag">
                    <el-icon size="14"><Collection /></el-icon>
                    {{ item.category }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="还没有从错题中掌握的题目" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PriceTag, Collection, Clock } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const activeTab = ref('wrong')
const wrongData = ref({
  wrong_answers: [],
  mastered: [],
  wrong_count: 0,
  mastered_count: 0,
})

onMounted(() => {
  fetchWrongAnswers()
})

const fetchWrongAnswers = async () => {
  try {
    const res = await request.get('/exercise/wrong-answers')
    wrongData.value = res
  } catch (error) {
    console.error('获取错题本失败:', error)
  }
}

const goToExercise = (id) => {
  router.push(`/exercises/${id}`)
}

const getDifficultyType = (d) => {
  const map = { beginner: 'success', intermediate: 'warning', advanced: 'danger' }
  return map[d] || 'info'
}

const getDifficultyText = (d) => {
  const map = { beginner: '初级', intermediate: '中级', advanced: '高级' }
  return map[d] || d
}
</script>

<style scoped>
.wrong-answers-page {
  padding: 40px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-page);
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 24px;
}

.page-header {
  margin-bottom: 36px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px;
}

.page-desc {
  font-size: 16px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.stats-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 36px;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 28px;
  border-radius: 16px;
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  flex: 1;
  transition: all 0.3s ease;
}

.stat-chip:hover {
  transform: translateY(-2px);
  box-shadow: var(--tm-shadow-glow);
}

.stat-chip.wrong {
  border-left: 3px solid rgba(255, 107, 107, 0.6);
}

.stat-chip.mastered {
  border-left: 3px solid rgba(81, 207, 102, 0.6);
}

.stat-num {
  font-size: 32px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.stat-chip.wrong .stat-num {
  color: #FF6B6B;
}

.stat-chip.mastered .stat-num {
  color: #51CF66;
}

.stat-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wrong-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 14px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.wrong-card:hover {
  transform: translateY(-3px) translateX(4px);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.wrong-card-left {
  flex-shrink: 0;
}

.wrong-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 107, 107, 0.1);
  color: #FF6B6B;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
}

.mastered-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(81, 207, 102, 0.1);
  color: #51CF66;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
}

.wrong-card-body {
  flex: 1;
  min-width: 0;
}

.wrong-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.wrong-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wrong-badges {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.wrong-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.wrong-card-action {
  flex-shrink: 0;
}

.mastered-card {
  opacity: 0.7;
}

.mastered-card:hover {
  opacity: 1;
}
</style>
