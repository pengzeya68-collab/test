<template>
  <div class="lp-detail-container">
    <div class="loading" v-if="loading">
      <div class="spinner">⏳</div>
    </div>

    <div v-if="!loading && path" class="path-content">
      <!-- 头部信息 -->
      <section class="path-hero">
        <div class="hero-tags">
          <span class="tag" :class="'stage-' + (path.stage || 1)">阶段{{ path.stage }}</span>
          <span class="tag" :class="'diff-' + (path.difficulty || 'beginner')">{{ getDifficultyText(path.difficulty) }}</span>
          <span class="tag tag-lang">{{ path.language }}</span>
        </div>
        <h1 class="hero-title">{{ path.title }}</h1>
        <p class="hero-desc">{{ path.description }}</p>

        <!-- 学习进度 -->
        <div class="progress-bar-wrap" v-if="isLoggedIn">
          <div class="pb-header">
            <span class="pb-label">学习进度</span>
            <span class="pb-stats">已完成 {{ progressData.completed_exercises }}/{{ progressData.total_exercises }} 题</span>
            <span class="pb-pct">{{ progressData.progress_percent }}%</span>
          </div>
          <div class="pb-track">
            <div class="pb-fill" :style="{ width: progressData.progress_percent + '%' }"></div>
          </div>
        </div>

        <!-- 完成庆祝 -->
        <div class="completion-banner" v-if="isLoggedIn && progressData.progress_percent >= 100">
          <div class="cb-icon">🎉</div>
          <div class="cb-text">
            <h3>恭喜完成本路径全部习题！</h3>
            <p>你已经掌握了这条学习路线的所有知识点，继续挑战下一个阶段吧！</p>
          </div>
          <button class="primary-btn" @click="goToNextStage">下一阶段 →</button>
        </div>

        <div class="hero-stats">
          <div class="hs-item">
            <span class="hs-emoji">⏱️</span>
            <span class="hs-val">{{ path.estimated_hours }}</span>
            <span class="hs-lbl">小时</span>
          </div>
          <div class="hs-item">
            <span class="hs-emoji">📄</span>
            <span class="hs-val">{{ path.exercises?.length || 0 }}</span>
            <span class="hs-lbl">个习题</span>
          </div>
          <div class="hs-item">
            <span class="hs-emoji">📅</span>
            <span class="hs-val">{{ formatDate(path.created_at) }}</span>
            <span class="hs-lbl">更新时间</span>
          </div>
        </div>

        <div class="hero-actions">
          <button class="primary-btn btn-lg" @click="startLearning">
            {{ progressData.completed_exercises > 0 ? '继续学习' : '开始学习' }}
          </button>
          <button class="outline-btn btn-lg" @click="toggleCollect">
            {{ isCollected ? '取消收藏' : '加入收藏' }}
          </button>
        </div>
      </section>

      <!-- 课程与习题 Tab -->
      <section class="content-section">
        <div class="custom-tabs">
          <button class="ctab" :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">
            📖 课程内容 <span class="ctab-badge" v-if="lessons.length > 0">{{ lessons.length }}节</span>
          </button>
          <button class="ctab" :class="{ active: activeTab === 'exercises' }" @click="activeTab = 'exercises'">
            ✏️ 练习题 <span class="ctab-badge" v-if="path?.exercises?.length > 0">{{ path.exercises.length }}题</span>
          </button>
          <button class="ctab" :class="{ active: activeTab === 'project' }" @click="activeTab = 'project'">
            🚀 项目实战
          </button>
        </div>

        <!-- 课程内容 -->
        <div v-show="activeTab === 'lessons'" class="tab-panel">
          <div v-if="!lessonsLoading" class="lesson-list">
            <div
              class="lesson-card"
              v-for="lesson in lessons"
              :key="lesson.id"
              @click="goToLesson(lesson.id)"
            >
              <div class="lc-num">{{ lesson.sort_order }}</div>
              <div class="lc-body">
                <h3 class="lc-title">{{ lesson.title }}</h3>
                <div class="lc-meta">
                  <span v-if="lesson.knowledge_point" class="lc-meta-item">🏷️ {{ lesson.knowledge_point }}</span>
                  <span class="lc-meta-item">⏰ {{ lesson.time_estimate }}分钟</span>
                </div>
              </div>
              <div class="lc-arrow">→</div>
            </div>
            <div class="empty-block" v-if="lessons.length === 0">
              <p>📭 该路径暂无课程内容</p>
            </div>
          </div>
        </div>

        <!-- 练习题 -->
        <div v-show="activeTab === 'exercises'" class="tab-panel">
          <div class="exercise-list">
            <div
              class="ex-card"
              :class="{ done: isExerciseCompleted(exercise.id) }"
              v-for="exercise in path?.exercises"
              :key="exercise.id"
              @click="goToExercise(exercise.id)"
            >
              <div class="ex-top">
                <div class="ex-title-row">
                  <span class="ex-status" v-if="isExerciseCompleted(exercise.id)">✅</span>
                  <span class="ex-status pending" v-else>⬜</span>
                  <h4 class="ex-title">{{ exercise.title }}</h4>
                </div>
                <div class="ex-badges">
                  <span class="badge badge-success" v-if="getExerciseScore(exercise.id)">{{ getExerciseScore(exercise.id) }}分</span>
                  <span class="badge" :class="'badge-' + (exercise.difficulty || 'beginner')">{{ getDifficultyText(exercise.difficulty) }}</span>
                </div>
              </div>
              <p class="ex-desc">{{ exercise.description }}</p>
              <div class="ex-footer">
                <span class="ex-foot-item">⏱️ {{ exercise.time_estimate }}分钟</span>
                <span class="ex-foot-item" v-if="exercise.knowledge_point">🏷️ {{ exercise.knowledge_point }}</span>
                <span class="ex-foot-item">📁 {{ exercise.category }}</span>
                <span class="ex-foot-item" v-if="getExerciseAttempts(exercise.id) > 0">✍️ 尝试 {{ getExerciseAttempts(exercise.id) }} 次</span>
              </div>
            </div>
            <div class="empty-block" v-if="!path?.exercises?.length">
              <p>📭 该路径暂无习题</p>
            </div>
          </div>
        </div>

        <!-- 项目实战 -->
        <div v-show="activeTab === 'project'" class="tab-panel">
          <ProjectPractice :pathId="pathId" />
        </div>
      </section>
    </div>

    <!-- 不存在 -->
    <div class="empty-page" v-if="!loading && !path">
      <div class="empty-icon">🔍</div>
      <p>学习路径不存在</p>
      <button class="primary-btn" @click="goBack">返回列表</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import ProjectPractice from './ProjectPractice.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)

const path = ref(null)
const loading = ref(false)
const pathId = route.params.id
const isCollected = ref(false)
const activeTab = ref('lessons')
const lessons = ref([])
const lessonsLoading = ref(false)
const progressData = ref({
  total_exercises: 0,
  completed_exercises: 0,
  progress_percent: 0,
  exercises: [],
})

onMounted(() => {
  fetchPathDetail()
  fetchLessons()
  if (isLoggedIn.value) fetchProgress()
})

const fetchPathDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/learning-paths/${pathId}`)
    path.value = res
  } catch (error) {
    ElMessage.error('获取学习路径详情失败')
  } finally {
    loading.value = false
  }
}

const fetchProgress = async () => {
  try {
    const res = await request.get(`/learning-paths/${pathId}/progress`)
    progressData.value = res
  } catch {}
}

const isExerciseCompleted = (id) => {
  return progressData.value.exercises?.find(e => e.id === id)?.completed || false
}

const getExerciseScore = (id) => {
  return progressData.value.exercises?.find(e => e.id === id)?.score
}

const getExerciseAttempts = (id) => {
  return progressData.value.exercises?.find(e => e.id === id)?.attempts || 0
}

const getDifficultyText = (d) => ({ beginner: '初级', intermediate: '中级', advanced: '高级' }[d] || d)

const formatDate = (ds) => ds ? new Date(ds).toLocaleDateString('zh-CN') : ''

const goToExercise = (id) => router.push(`/exercises/${id}`)

const goBack = () => router.back()

const startLearning = () => {
  if (lessons.value.length > 0) {
    const nextLesson = lessons.value[0]
    router.push(`/learning-paths/${pathId}/lessons/${nextLesson.id}`)
  } else if (path.value?.exercises?.length > 0) {
    const nextEx = progressData.value.exercises?.find(e => !e.completed)
    const targetId = nextEx?.id || path.value.exercises[0]?.id
    if (targetId) {
      router.push(`/exercises/${targetId}`)
    } else {
      ElMessage.info('该路径暂无可用习题')
    }
  } else {
    ElMessage.info('该路径暂无课程和习题')
  }
}

const goToNextStage = () => {
  const ns = (path.value?.stage || 0) + 1
  router.push(ns <= 5 ? { path: '/learning-paths', query: { stage: ns } } : '/skill-analysis')
}

const toggleCollect = async () => {
  try {
    if (isCollected.value) {
      await request.delete(`/learning-paths/${pathId}/collect`)
    } else {
      await request.post(`/learning-paths/${pathId}/collect`)
    }
    isCollected.value = !isCollected.value
    ElMessage.success(isCollected.value ? '收藏成功' : '取消收藏成功')
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

const fetchLessons = async () => {
  lessonsLoading.value = true
  try {
    const res = await request.get(`/learning-paths/${pathId}/lessons`)
    lessons.value = res.lessons || []
  } catch {} finally { lessonsLoading.value = false }
}

const goToLesson = (lid) => router.push(`/learning-paths/${pathId}/lessons/${lid}`)
</script>

<style scoped>
.lp-detail-container {
  width: 100%;
  padding: 40px 60px;
  box-sizing: border-box;
}

.loading {
  text-align: center;
  padding: 120px 0;
}
.spinner { font-size: 40px; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.path-hero {
  background: var(--tm-card-bg);
  border-radius: 16px;
  padding: 36px 40px;
  margin-bottom: 28px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.hero-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
}

.tag {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}

.stage-1 { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.25); }
.stage-2 { background: rgba(34, 211, 238, 0.15); color: #22d3ee; border: 1px solid rgba(34, 211, 238, 0.25); }
.stage-3 { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.25); }
.stage-4 { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.25); }
.stage-5 { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.25); }
.tag-lang { background: rgba(139, 92, 246, 0.1); color: var(--tm-color-primary-dark); border: 1px solid rgba(139, 92, 246, 0.2); }

.diff-beginner { background: rgba(52, 211, 153, 0.12); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.25); }
.diff-intermediate { background: rgba(245, 158, 11, 0.12); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.25); }
.diff-advanced { background: rgba(239, 68, 68, 0.12); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.25); }

.hero-title {
  font-size: 30px;
  font-weight: 800;
  color: var(--tm-text-primary);
  margin: 0 0 14px;
  letter-spacing: -0.5px;
}

.hero-desc {
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.7;
  margin: 0 0 22px;
}

.progress-bar-wrap {
  background: rgba(139, 92, 246, 0.06);
  border-radius: 10px;
  padding: 18px 22px;
  margin-bottom: 22px;
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.pb-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.pb-label { font-size: 15px; font-weight: 600; color: var(--tm-text-primary); }
.pb-stats { font-size: 13px; color: var(--tm-text-regular); }
.pb-pct { margin-left: auto; font-size: 20px; font-weight: 700; color: var(--tm-color-primary); }

.pb-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.pb-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 4px;
  transition: width 0.6s ease;
}

.completion-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 22px 26px;
  background: rgba(52, 211, 153, 0.06);
  border-radius: 12px;
  border: 1px solid rgba(52, 211, 153, 0.18);
  margin-bottom: 22px;
}

.cb-icon { font-size: 42px; flex-shrink: 0; }
.cb-text h3 { font-size: 17px; font-weight: 700; color: #34d399; margin: 0 0 4px; }
.cb-text p { font-size: 13px; color: var(--tm-text-regular); margin: 0; line-height: 1.5; }

.hero-stats {
  display: flex;
  gap: 36px;
  margin-bottom: 26px;
  padding: 20px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.hs-item { display: flex; align-items: center; gap: 8px; }
.hs-emoji { font-size: 20px; }
.hs-val { font-size: 22px; font-weight: 800; color: var(--tm-text-primary); }
.hs-lbl { font-size: 13px; color: var(--tm-text-secondary); }

.hero-actions { display: flex; gap: 14px; }

.primary-btn {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.15s;
}
.primary-btn:hover { opacity: 0.9; transform: translateY(-1px); }

.outline-btn {
  background: transparent;
  color: var(--tm-text-primary);
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.outline-btn:hover { border-color: var(--tm-color-primary); color: var(--tm-color-primary); }

.btn-lg { padding: 12px 32px; font-size: 15px; }

.content-section {
  background: var(--tm-card-bg);
  border-radius: 16px;
  padding: 28px 32px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.custom-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 0;
}

.ctab {
  background: none;
  border: none;
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-secondary);
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ctab.active {
  color: var(--tm-text-primary);
}

.ctab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px 3px 0 0;
}

.ctab-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(139, 92, 246, 0.15);
  color: var(--tm-color-primary);
}

.tab-panel { min-height: 200px; }

/* ===== 课程列表 ===== */
.lesson-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lesson-card {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s;
}

.lesson-card:hover {
  background: rgba(139, 92, 246, 0.06);
  border-color: rgba(139, 92, 246, 0.2);
  transform: translateX(4px);
}

.lc-num {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.lc-body { flex: 1; min-width: 0; }

.lc-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 8px;
  line-height: 1.4;
}

.lc-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.lc-meta-item { display: flex; align-items: center; gap: 4px; }

.lc-arrow {
  color: var(--tm-text-secondary);
  font-size: 20px;
  flex-shrink: 0;
  transition: transform 0.2s, color 0.2s;
}

.lesson-card:hover .lc-arrow {
  transform: translateX(4px);
  color: var(--tm-color-primary);
}

/* ===== 习题列表 ===== */
.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ex-card {
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s;
}

.ex-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(139, 92, 246, 0.15);
  transform: translateX(4px);
}

.ex-card.done {
  border-left: 3px solid #34d399;
  background: rgba(52, 211, 153, 0.03);
}

.ex-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ex-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ex-status { font-size: 18px; flex-shrink: 0; }
.ex-status.pending { opacity: 0.35; }

.ex-title { font-size: 16px; font-weight: 700; color: var(--tm-text-primary); margin: 0; }

.ex-badges { display: flex; gap: 8px; align-items: center; }

.badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
}

.badge-success { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.badge-beginner { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.badge-intermediate { background: rgba(245, 158, 11, 0.12); color: #f59e0b; }
.badge-advanced { background: rgba(239, 68, 68, 0.12); color: #ef4444; }

.ex-desc {
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0 0 14px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  font-size: 14px;
}

.ex-footer {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.ex-foot-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.empty-block {
  text-align: center;
  padding: 60px 0;
  color: var(--tm-text-secondary);
  font-size: 15px;
}

.empty-page {
  text-align: center;
  padding: 80px 0;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-page p { color: var(--tm-text-secondary); margin-bottom: 20px; font-size: 16px; }

@media (max-width: 1200px) {
  .lp-detail-container { padding: 24px 20px; }
  .hero-stats { gap: 20px; flex-wrap: wrap; }
  .hero-actions { flex-direction: column; }
  .btn-lg { width: 100%; }
}
</style>