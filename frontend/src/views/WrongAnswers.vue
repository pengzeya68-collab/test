<template>
  <div class="wrong-answers-page">
    <header class="page-header">
      <div class="header-titles">
        <h1 class="page-title">馃摉 閿欓鏈</h1>
        <p class="page-desc">鍥為【閿欓锛屾煡婕忚ˉ缂猴紝閬垮厤閲嶅鐘敊</p>
      </div>
      <div class="title-glow-line"></div>
    </header>

    <div class="stats-bar">
      <div class="stat-chip stat-wrong">
        <div class="stat-icon-box stat-icon-wrong">鉁</div>
        <div class="stat-info">
          <span class="stat-num stat-num-wrong">{{ wrongData.wrong_count }}</span>
          <span class="stat-label">寰呭涔</span>
        </div>
      </div>
      <div class="stat-chip stat-mastered">
        <div class="stat-icon-box stat-icon-mastered">鉁</div>
        <div class="stat-info">
          <span class="stat-num stat-num-mastered">{{ wrongData.mastered_count }}</span>
          <span class="stat-label">宸叉帉鎻</span>
        </div>
      </div>
    </div>

    <div class="tabs-container">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'wrong' }"
        @click="activeTab = 'wrong'"
      >鉂?寰呭涔</div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'mastered' }"
        @click="activeTab = 'mastered'"
      >鉁?宸叉帉鎻</div>
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
              <div class="card-status-icon icon-fail">鉁</div>
            </div>
            <div class="card-body" @click="goToExercise(item.id)">
              <div class="card-title-row">
                <h3 class="card-title">{{ item.title }}</h3>
              </div>
              <div class="card-meta">
                <span v-if="item.knowledge_point" class="meta-tag">
                  <span class="meta-emoji">馃彿锔</span>
                  {{ item.knowledge_point }}
                </span>
                <span v-if="item.category" class="meta-tag">
                  <span class="meta-emoji">馃搧</span>
                  {{ item.category }}
                </span>
                <span class="meta-tag">
                  <span class="meta-emoji">鈴</span>
                  {{ item.last_wrong_at }}
                </span>
              </div>
            </div>
            <div class="card-right">
              <span class="badge badge-danger">閿?{{ item.wrong_count }} 娆</span>
              <span class="badge" :class="'badge-' + getDifficultyType(item.difficulty)">
                {{ getDifficultyText(item.difficulty) }}
              </span>
              <button class="redo-btn" @click.stop="goToExercise(item.id)">閲嶅仛</button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-emoji">馃帀</div>
          <p class="empty-title">娌℃湁閿欓锛岀户缁繚鎸侊紒</p>
          <p class="empty-desc">浣犵殑鐭ヨ瘑鎺屾彙寰楀緢鎵庡疄</p>
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
              <div class="card-status-icon icon-pass">鉁</div>
            </div>
            <div class="card-body" @click="goToExercise(item.id)">
              <div class="card-title-row">
                <h3 class="card-title">{{ item.title }}</h3>
              </div>
              <div class="card-meta">
                <span v-if="item.knowledge_point" class="meta-tag">
                  <span class="meta-emoji">馃彿锔</span>
                  {{ item.knowledge_point }}
                </span>
                <span v-if="item.category" class="meta-tag">
                  <span class="meta-emoji">馃搧</span>
                  {{ item.category }}
                </span>
              </div>
            </div>
            <div class="card-right">
              <span class="badge badge-success">宸叉帉鎻</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-emoji">馃摑</div>
          <p class="empty-title">杩樻病鏈変粠閿欓涓帉鎻＄殑棰樼洰</p>
          <p class="empty-desc">缁х画澶嶄範閿欓锛屾妸瀹冧滑鍙樻垚浣犵殑寮洪」</p>
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
    console.error('鑾峰彇閿欓鏈け璐?', error)
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
  const map = { beginner: '鍒濈骇', intermediate: '涓骇', advanced: '楂樼骇', easy: '鍒濈骇', medium: '涓骇', hard: '楂樼骇' }
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
  background: color-mix(in srgb, var(--tm-color-danger) 12%, transparent);
  color: var(--tm-color-danger);
}

.stat-icon-mastered {
  background: color-mix(in srgb, var(--tm-color-success) 12%, transparent);
  color: var(--tm-color-success);
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
  color: var(--tm-color-danger);
}

.stat-num-mastered {
  color: var(--tm-color-success);
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
  background: color-mix(in srgb, var(--tm-color-danger) 12%, transparent);
  color: var(--tm-color-danger);
}

.icon-pass {
  background: color-mix(in srgb, var(--tm-color-success) 12%, transparent);
  color: var(--tm-color-success);
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
  background: color-mix(in srgb, var(--tm-color-danger) 15%, transparent);
  color: var(--tm-color-danger);
}

.badge-success {
  background: color-mix(in srgb, var(--tm-color-success) 15%, transparent);
  color: var(--tm-color-success);
}

.badge-warning {
  background: color-mix(in srgb, var(--tm-color-warning) 15%, transparent);
  color: var(--tm-color-warning);
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
