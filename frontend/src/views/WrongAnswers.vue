<template>
  <div class="wrong-answers-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">📖 错题本</h1>
        <p class="page-desc">回顾错题，查漏补缺，避免重复犯错</p>
      </div>
      <div class="title-glow-line"></div>
    </header>

    <div class="stats-bar">
      <div class="stat-chip stat-wrong">
        <div class="stat-icon-box stat-icon-wrong">✗</div>
        <div class="stat-info">
          <span class="stat-num stat-num-wrong">{{ wrongData.wrong_count }}</span>
          <span class="stat-label">待复习</span>
        </div>
      </div>
      <div class="stat-chip stat-mastered">
        <div class="stat-icon-box stat-icon-mastered">✓</div>
        <div class="stat-info">
          <span class="stat-num stat-num-mastered">{{ wrongData.mastered_count }}</span>
          <span class="stat-label">已掌握</span>
        </div>
      </div>
    </div>

    <div class="tabs-container">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'wrong' }"
        @click="activeTab = 'wrong'"
      >❌ 待复习</div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'mastered' }"
        @click="activeTab = 'mastered'"
      >✅ 已掌握</div>
    </div>

    <div class="tab-content">
      <template v-if="activeTab === 'wrong'">
        <div class="card-list" v-if="wrongData.wrong_answers.length > 0">
          <div
            v-for="item in wrongData.wrong_answers"
            :key="item.id"
            class="wrong-card"
          >
            <div class="card-left">
              <div class="card-status-icon icon-fail">✗</div>
            </div>
            <div class="card-body" @click="goToExercise(item.id)">
              <div class="card-title-row">
                <h3 class="card-title">{{ item.title }}</h3>
              </div>
              <div class="card-meta">
                <span v-if="item.knowledge_point" class="meta-tag">
                  <span class="meta-emoji">🏷️</span>
                  {{ item.knowledge_point }}
                </span>
                <span v-if="item.category" class="meta-tag">
                  <span class="meta-emoji">📁</span>
                  {{ item.category }}
                </span>
                <span class="meta-tag">
                  <span class="meta-emoji">⏰</span>
                  {{ item.last_wrong_at }}
                </span>
              </div>
            </div>
            <div class="card-right">
              <span class="badge badge-danger">错 {{ item.wrong_count }} 次</span>
              <span class="badge" :class="'badge-' + getDifficultyType(item.difficulty)">
                {{ getDifficultyText(item.difficulty) }}
              </span>
              <button class="redo-btn" @click.stop="goToExercise(item.id)">重做</button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-emoji">🎉</div>
          <p class="empty-title">没有错题，继续保持！</p>
          <p class="empty-desc">你的知识掌握得很扎实</p>
        </div>
      </template>

      <template v-if="activeTab === 'mastered'">
        <div class="card-list" v-if="wrongData.mastered.length > 0">
          <div
            v-for="item in wrongData.mastered"
            :key="item.id"
            class="wrong-card mastered-card"
          >
            <div class="card-left">
              <div class="card-status-icon icon-pass">✓</div>
            </div>
            <div class="card-body" @click="goToExercise(item.id)">
              <div class="card-title-row">
                <h3 class="card-title">{{ item.title }}</h3>
              </div>
              <div class="card-meta">
                <span v-if="item.knowledge_point" class="meta-tag">
                  <span class="meta-emoji">🏷️</span>
                  {{ item.knowledge_point }}
                </span>
                <span v-if="item.category" class="meta-tag">
                  <span class="meta-emoji">📁</span>
                  {{ item.category }}
                </span>
              </div>
            </div>
            <div class="card-right">
              <span class="badge badge-success">已掌握</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-emoji">📝</div>
          <p class="empty-title">还没有从错题中掌握的题目</p>
          <p class="empty-desc">继续复习错题，把它们变成你的强项</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
    wrongData.value = {
      wrong_answers: res.wrong_answers || [],
      mastered: res.mastered || [],
      wrong_count: res.wrong_count || 0,
      mastered_count: res.mastered_count || 0,
    }
  } catch (error) {
    console.error('获取错题本失败:', error)
  }
}

const goToExercise = (id) => {
  router.push(`/exercises/${id}`)
}

const getDifficultyType = (d) => {
  const map = { beginner: 'success', intermediate: 'warning', advanced: 'danger', easy: 'success', medium: 'warning', hard: 'danger' }
  return map[d] || 'info'
}

const getDifficultyText = (d) => {
  const map = { beginner: '初级', intermediate: '中级', advanced: '高级', easy: '初级', medium: '中级', hard: '高级' }
  return map[d] || d
}
</script>

<style scoped>
.wrong-answers-page {
  width: 100%;
  padding: 40px 60px;
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--tm-bg-page);
}

.page-header {
  margin-bottom: 32px;
}

.header-titles {
  margin-bottom: 4px;
}

.page-title {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px;
}

.page-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
}

.title-glow-line {
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark), transparent);
  margin-top: 16px;
  border-radius: 1px;
}

.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 28px;
}

.stat-chip {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 14px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  transition: all 0.3s ease;
}

.stat-chip:hover {
  border-color: var(--border-subtle);
  background: var(--tm-card-bg);
}

.stat-icon-box {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  flex-shrink: 0;
}

.stat-icon-wrong {
  background: rgba(248, 113, 113, 0.12);
  color: #f87171;
}

.stat-icon-mastered {
  background: rgba(52, 211, 153, 0.12);
  color: #34d399;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-num {
  font-size: 30px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.stat-num-wrong {
  color: #f87171;
}

.stat-num-mastered {
  color: #34d399;
}

.stat-label {
  font-size: 13px;
  color: var(--tm-text-regular);
}

.tabs-container {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--tm-border-light);
  padding-bottom: 0;
}

.tab-item {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.25s ease;
  user-select: none;
}

.tab-item:hover {
  color: var(--tm-text-regular);
}

.tab-item.active {
  color: var(--tm-text-primary);
  border-bottom-color: var(--tm-color-primary);
  font-weight: 600;
}

.tab-content {
  min-height: 400px;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wrong-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 22px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.wrong-card:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.25);
  background: var(--tm-card-bg);
  transform: translateX(4px);
}

.mastered-card {
  opacity: 0.6;
}

.mastered-card:hover {
  opacity: 1;
}

.card-left {
  flex-shrink: 0;
}

.card-status-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
}

.icon-fail {
  background: rgba(248, 113, 113, 0.12);
  color: #f87171;
}

.icon-pass {
  background: rgba(52, 211, 153, 0.12);
  color: #34d399;
}

.card-body {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.card-title-row {
  margin-bottom: 6px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12.5px;
  color: var(--tm-text-secondary);
}

.meta-emoji {
  font-size: 12px;
}

.card-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.badge-danger {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.badge-info {
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
}

.redo-btn {
  padding: 7px 18px;
  border-radius: 8px;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.4);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  color: var(--tm-color-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.redo-btn:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  border-color: rgba(var(--tm-color-primary-rgb), 0.6);
  color: var(--tm-color-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-emoji {
  font-size: 56px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-regular);
  margin: 0 0 6px;
}

.empty-desc {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin: 0;
}
</style>