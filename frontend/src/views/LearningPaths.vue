<template>
  <div class="learning-paths" style="position: relative; z-index: 1;">
    <div class="cyber-grid-bg" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: -1;"></div>

    <div class="quick-stats" v-if="isLoggedIn">
      <div class="stat-card">
        <div class="stat-icon-wrap stat-icon-green">
          <el-icon :size="22"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ displayCompleted }}</div>
          <div class="stat-label">已完成习题</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap stat-icon-orange">
          <el-icon :size="22"><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ displayStreak }}<small> 天</small></div>
          <div class="stat-label">连续学习</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap stat-icon-purple">
          <el-icon :size="22"><DataAnalysis /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ skillLevel }}</div>
          <div class="stat-label">技能等级</div>
        </div>
      </div>
    </div>

    <div class="lp-layout">
      <div class="mobile-stage-tabs">
        <div
          class="mobile-tab"
          v-for="stage in stageConfigs"
          :key="stage.id"
          :class="{ active: currentStage === stage.id }"
          @click="switchStage(stage.id)"
        >
          <span class="mobile-tab-num">{{ stage.id }}</span>
          <span class="mobile-tab-title">{{ stage.shortTitle }}</span>
        </div>
      </div>

      <aside class="lp-sidebar">
        <div class="sidebar-header">
          <el-icon :size="18"><Reading /></el-icon>
          <span>学习路线</span>
        </div>
        <div class="sidebar-stages">
          <div
            class="sidebar-stage"
            v-for="stage in stageConfigs"
            :key="stage.id"
            :class="{ active: currentStage === stage.id }"
            @click="switchStage(stage.id)"
          >
            <div class="stage-num-badge">
              <el-icon v-if="isLoggedIn && getStageProgress(stage.id) >= 100" :size="18" style="color:#4ADE80"><CircleCheck /></el-icon>
              <span v-else>{{ stage.id }}</span>
            </div>
            <div class="stage-body">
              <div class="stage-title">{{ stage.shortTitle }}</div>
              <div class="stage-desc">{{ stage.desc }}</div>
              <div class="stage-progress-mini">
                <div class="progress-track">
                  <div class="progress-fill" :style="{ width: getStageProgress(stage.id) + '%' }"></div>
                </div>
                <span class="progress-pct">{{ getStageProgress(stage.id) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <main class="lp-main">
        <div class="hero-banner" :class="'hero-stage-' + currentStage">
          <div class="hero-deco"></div>
          <div class="hero-content">
            <div class="hero-badge">阶段 {{ currentStage }}</div>
            <h2 class="hero-title">{{ stageInfo.title }}</h2>
            <p class="hero-desc">{{ stageInfo.description }}</p>
            <div class="hero-meta">
              <div class="hero-meta-item">
                <el-icon><Timer /></el-icon>
                <span>预计 {{ currentStageStats.hours }} 小时</span>
              </div>
              <div class="hero-meta-item">
                <el-icon><Document /></el-icon>
                <span>{{ currentStageStats.exercises }} 个习题</span>
              </div>
              <div class="hero-meta-item">
                <el-icon><Collection /></el-icon>
                <span>{{ currentStageStats.paths }} 条路径</span>
              </div>
            </div>
          </div>
        </div>

        <div class="content-toolbar">
          <div class="toolbar-left">
            <h3 class="section-title">课程列表</h3>
            <span class="result-count">共 {{ learningPaths.length }} 条</span>
          </div>
          <div class="toolbar-right">
            <el-select
              v-model="currentDifficulty"
              placeholder="难度筛选"
              @change="fetchLearningPaths"
              style="width: 130px;"
            >
              <el-option label="全部难度" value="" />
              <el-option label="初级" value="beginner" />
              <el-option label="中级" value="intermediate" />
              <el-option label="高级" value="advanced" />
            </el-select>
          </div>
        </div>

        <div class="path-list" v-if="learningPaths.length > 0 && !loading">
          <div class="path-list-header">
            <span class="col-icon"></span>
            <span class="col-title">路径名称</span>
            <span class="col-count">习题</span>
            <span class="col-hours">时长</span>
            <span class="col-diff">难度</span>
            <span class="col-action">操作</span>
          </div>
          <div
            class="path-row"
            v-for="path in learningPaths"
            :key="path.id"
            @click="goToDetail(path.id)"
          >
            <div class="col-icon">
              <span class="lang-icon">{{ getLanguageIcon(path.language) }}</span>
            </div>
            <div class="col-title">
              <div class="path-name">
                <el-icon v-if="isLoggedIn && isPathCompleted(path.id)" class="completed-check" :size="16"><CircleCheck /></el-icon>
                {{ path.title }}
              </div>
              <div class="path-desc-snippet">{{ path.description }}</div>
              <div class="path-progress-inline" v-if="isLoggedIn && getPathProgress(path.id)">
                <div class="progress-bar-mini">
                  <div class="progress-fill" :style="{ width: getPathProgress(path.id).progress_percent + '%', background: getPathProgressColor(path.id) }"></div>
                </div>
                <span class="progress-label">{{ getPathProgress(path.id).completed_exercises }}/{{ getPathProgress(path.id).total_exercises }}</span>
              </div>
            </div>
            <div class="col-count">{{ path.exercise_count }}</div>
            <div class="col-hours">{{ path.estimated_hours }}h</div>
            <div class="col-diff">
              <span class="difficulty-badge" :class="'diff-' + path.difficulty">{{ getDifficultyText(path.difficulty) }}</span>
            </div>
            <div class="col-action">
              <el-button type="primary" size="small" @click.stop="goToDetail(path.id)">
                {{ isLoggedIn && isPathCompleted(path.id) ? '复习' : (isLoggedIn && getPathProgress(path.id)?.completed_exercises > 0 ? '继续' : '开始') }}
              </el-button>
            </div>
          </div>
        </div>

        <div class="empty-state" v-if="learningPaths.length === 0 && !loading">
          <el-empty description="该阶段暂无学习路径" />
        </div>

        <div class="loading-state" v-if="loading">
          <el-icon class="is-loading" :size="36"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timer, Document, Collection, Loading, CircleCheck, Reading, DataAnalysis } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)

const learningPaths = ref([])
const allPaths = ref([])
const loading = ref(false)
const currentStage = ref(1)
const currentDifficulty = ref('')
const allProgress = ref([])

const displayCompleted = ref(0)
const displayStreak = ref(0)

const stageConfigs = [
  { id: 1, shortTitle: '测试入门筑基', desc: '零基础入门，掌握测试基础', estimatedWeeks: 4 },
  { id: 2, shortTitle: '功能测试精通', desc: '精通各类项目功能测试', estimatedWeeks: 8 },
  { id: 3, shortTitle: '测试技术进阶', desc: '接口、Linux、性能测试', estimatedWeeks: 12 },
  { id: 4, shortTitle: '自动化测试专家', desc: 'Python、接口/UI自动化', estimatedWeeks: 16 },
  { id: 5, shortTitle: '测试架构师之路', desc: '平台开发、DevOps、质量体系', estimatedWeeks: 20 },
]

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

const totalCompletedExercises = computed(() => {
  return allProgress.value.reduce((sum, p) => sum + (p.completed_exercises || 0), 0)
})

const skillLevel = computed(() => {
  const total = totalCompletedExercises.value
  if (total >= 100) return '专家'
  if (total >= 60) return '高级'
  if (total >= 30) return '中级'
  if (total >= 10) return '初级'
  return '入门'
})

const currentStageStats = computed(() => {
  const paths = learningPaths.value
  return {
    hours: paths.reduce((sum, p) => sum + (p.estimated_hours || 0), 0),
    exercises: paths.reduce((sum, p) => sum + (p.exercise_count || 0), 0),
    paths: paths.length
  }
})

const stageProgressMap = computed(() => {
  const map = {}
  for (let i = 1; i <= 5; i++) {
    const stagePaths = allPaths.value.filter(p => p.stage === i)
    const stagePathIds = new Set(stagePaths.map(p => p.id))
    const stageProgressEntries = allProgress.value.filter(p => stagePathIds.has(p.path_id))
    const totalExercises = stageProgressEntries.reduce((sum, p) => sum + (p.total_exercises || 0), 0)
    const completedExercises = stageProgressEntries.reduce((sum, p) => sum + (p.completed_exercises || 0), 0)
    map[i] = totalExercises > 0 ? Math.round(completedExercises / totalExercises * 100) : 0
  }
  return map
})

const languageIconMap = {
  'Python': '🐍', 'Java': '☕', 'SQL': '🗃️', 'Linux': '🐧',
  'JavaScript': '📜', 'HTTP': '🌐', 'Shell': '💻', 'Bash': '💻',
  'HTML': '🌐', 'CSS': '🎨', 'Postman': '📮', 'JMeter': '📊',
  'Selenium': '🤖', 'Appium': '📱', 'Docker': '🐳', 'Git': '📂',
  '性能测试': '⚡', '接口测试': '🔌', '自动化': '🤖',
}

const animateValue = (refVar, target, duration = 800) => {
  const start = refVar.value
  const diff = target - start
  if (diff === 0) return
  const startTime = performance.now()
  const step = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    refVar.value = Math.round(start + diff * eased)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

onMounted(() => {
  if (route.query.stage) {
    currentStage.value = parseInt(route.query.stage)
  }
  fetchLearningPaths()
  if (isLoggedIn.value) {
    fetchAllPaths()
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

const fetchAllPaths = async () => {
  try {
    const res = await request.get('/learning-paths')
    allPaths.value = res
  } catch (error) {
    console.error('获取所有路径失败:', error)
  }
}

const fetchAllProgress = async () => {
  try {
    const res = await request.get('/learning-paths/all-progress')
    allProgress.value = res.progress || []
    // 从API返回数据计算 displayStreak 和 displayCompleted
    const streak = res.streak || res.streak_days || 0
    const completed = res.completed_exercises || totalCompletedExercises.value
    nextTick(() => {
      animateValue(displayCompleted, completed, 1000)
      animateValue(displayStreak, streak, 1000)
    })
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

const getStageProgress = (stageId) => {
  return stageProgressMap.value[stageId] || 0
}

const switchStage = (stageId) => {
  currentStage.value = stageId
  fetchLearningPaths()
}

const handleStageChange = () => {
  fetchLearningPaths()
}

const isPathCompleted = (pathId) => {
  const p = getPathProgress(pathId)
  return p && p.progress_percent >= 100
}

const getLanguageIcon = (lang) => {
  if (!lang) return '📘'
  for (const [key, icon] of Object.entries(languageIconMap)) {
    if (lang.toLowerCase().includes(key.toLowerCase())) return icon
  }
  return '📘'
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
  padding: 20px 0;
  min-height: 100%;
  width: 100%;
  box-sizing: border-box;
}

.cyber-grid-bg {
  background-image:
    linear-gradient(rgba(0, 242, 254, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 242, 254, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
  pointer-events: none;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-green {
  background: rgba(74, 222, 128, 0.12);
  color: #4ADE80;
}

.stat-icon-orange {
  background: rgba(250, 204, 21, 0.12);
  color: #FACC15;
}

.stat-icon-purple {
  background: rgba(168, 85, 247, 0.12);
  color: #A855F7;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--tm-text-primary);
  line-height: 1.2;
}

.stat-value small {
  font-size: 14px;
  font-weight: 400;
  color: var(--tm-text-secondary);
}

.stat-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.lp-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.mobile-stage-tabs {
  display: none;
  overflow-x: auto;
  gap: 8px;
  padding-bottom: 8px;
  margin-bottom: 16px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.mobile-stage-tabs::-webkit-scrollbar {
  display: none;
}

.mobile-tab {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 10px;
  background: var(--tm-glass-bg);
  border: var(--tm-glass-border);
  color: var(--tm-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.mobile-tab.active {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.35);
}

.mobile-tab-num {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.1);
}

.mobile-tab.active .mobile-tab-num {
  background: rgba(255, 255, 255, 0.25);
}

.lp-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  overflow: hidden;
  position: sticky;
  top: 20px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 20px 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary);
  border-bottom: 1px solid var(--tm-border-light);
}

.sidebar-stages {
  padding: 8px;
}

.sidebar-stage {
  display: flex;
  gap: 14px;
  padding: 14px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 3px solid transparent;
  margin-bottom: 4px;
}

.sidebar-stage:hover {
  background: var(--tm-bg-hover);
}

.sidebar-stage.active {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-left-color: var(--tm-color-primary);
  box-shadow: -4px 0 16px rgba(var(--tm-color-primary-rgb), 0.2);
}

.stage-num-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--tm-text-secondary);
  flex-shrink: 0;
  transition: all 0.3s;
}

.sidebar-stage.active .stage-num-badge {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  box-shadow: 0 4px 12px rgba(var(--tm-color-primary-rgb), 0.35);
}

.stage-body {
  flex: 1;
  min-width: 0;
}

.sidebar-stage .stage-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin-bottom: 3px;
  transition: color 0.3s;
}

.sidebar-stage.active .stage-title {
  color: var(--tm-color-primary);
}

.sidebar-stage .stage-desc {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-bottom: 8px;
  line-height: 1.4;
}

.stage-progress-mini {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-track {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.progress-track .progress-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-stage.active .progress-track .progress-fill {
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-light));
  box-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.4);
}

.progress-pct {
  font-size: 11px;
  color: var(--tm-text-secondary);
  font-weight: 500;
  min-width: 28px;
  text-align: right;
}

.sidebar-stage.active .progress-pct {
  color: var(--tm-color-primary);
}

.lp-main {
  flex: 1;
  min-width: 0;
}

.hero-banner {
  position: relative;
  border-radius: 16px;
  padding: 32px 36px;
  margin-bottom: 24px;
  overflow: hidden;
  border: var(--tm-glass-border);
}

.hero-stage-1 { background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.08), rgba(24, 24, 27, 0.9)); }
.hero-stage-2 { background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.08), rgba(24, 24, 27, 0.9)); }
.hero-stage-3 { background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(139, 92, 246, 0.08), rgba(24, 24, 27, 0.9)); }
.hero-stage-4 { background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(251, 146, 60, 0.08), rgba(24, 24, 27, 0.9)); }
.hero-stage-5 { background: linear-gradient(135deg, rgba(236, 72, 153, 0.15), rgba(244, 63, 94, 0.08), rgba(24, 24, 27, 0.9)); }

.hero-deco {
  position: absolute;
  top: -30px;
  right: -30px;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--tm-color-primary-rgb), 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
  background: rgba(var(--tm-color-primary-rgb), 0.15);
  color: var(--tm-color-primary);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.25);
}

.hero-stage-1 .hero-badge { background: rgba(34, 197, 94, 0.15); color: #22C55E; border-color: rgba(34, 197, 94, 0.25); }
.hero-stage-2 .hero-badge { background: rgba(59, 130, 246, 0.15); color: #3B82F6; border-color: rgba(59, 130, 246, 0.25); }
.hero-stage-3 .hero-badge { background: rgba(168, 85, 247, 0.15); color: #A855F7; border-color: rgba(168, 85, 247, 0.25); }
.hero-stage-4 .hero-badge { background: rgba(245, 158, 11, 0.15); color: #F59E0B; border-color: rgba(245, 158, 11, 0.25); }
.hero-stage-5 .hero-badge { background: rgba(236, 72, 153, 0.15); color: #EC4899; border-color: rgba(236, 72, 153, 0.25); }

.hero-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin-bottom: 8px;
  line-height: 1.3;
}

.hero-desc {
  font-size: 14px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
  max-width: 600px;
}

.hero-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.hero-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--tm-text-regular);
}

.hero-meta-item .el-icon {
  color: var(--tm-color-primary);
}

.content-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.toolbar-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
}

.result-count {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.path-list {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 14px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  overflow: hidden;
}

.path-list-header {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--tm-border-light);
  font-size: 12px;
  font-weight: 500;
  color: var(--tm-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.path-list-header .col-icon { width: 44px; flex-shrink: 0; }
.path-list-header .col-title { flex: 1; min-width: 0; }
.path-list-header .col-count { width: 64px; text-align: center; flex-shrink: 0; }
.path-list-header .col-hours { width: 64px; text-align: center; flex-shrink: 0; }
.path-list-header .col-diff { width: 72px; text-align: center; flex-shrink: 0; }
.path-list-header .col-action { width: 84px; text-align: center; flex-shrink: 0; }

.path-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--tm-border-light);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.path-row:last-child {
  border-bottom: none;
}

.path-row:hover {
  background: var(--tm-bg-hover);
}

.path-row:hover .path-name {
  color: var(--tm-color-primary);
}

.path-row .col-icon { width: 44px; flex-shrink: 0; }
.path-row .col-title { flex: 1; min-width: 0; padding-right: 16px; }
.path-row .col-count { width: 64px; text-align: center; flex-shrink: 0; font-size: 14px; color: var(--tm-text-regular); }
.path-row .col-hours { width: 64px; text-align: center; flex-shrink: 0; font-size: 14px; color: var(--tm-text-regular); }
.path-row .col-diff { width: 72px; text-align: center; flex-shrink: 0; }
.path-row .col-action { width: 84px; text-align: center; flex-shrink: 0; }

.lang-icon {
  font-size: 26px;
  line-height: 1;
}

.path-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  transition: color 0.25s;
}

.completed-check {
  color: #4ADE80;
}

.path-desc-snippet {
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
  margin-bottom: 6px;
}

.path-progress-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar-mini {
  width: 100px;
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-mini .progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-label {
  font-size: 11px;
  color: var(--tm-text-secondary);
  white-space: nowrap;
}

.difficulty-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.diff-beginner {
  background: rgba(74, 222, 128, 0.1);
  color: #4ADE80;
  border: 1px solid rgba(74, 222, 128, 0.2);
}

.diff-intermediate {
  background: rgba(250, 204, 21, 0.1);
  color: #FACC15;
  border: 1px solid rgba(250, 204, 21, 0.2);
}

.diff-advanced {
  background: rgba(248, 113, 113, 0.1);
  color: #F87171;
  border: 1px solid rgba(248, 113, 113, 0.2);
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--tm-text-secondary);
  font-size: 14px;
}

@media (max-width: 1024px) {
  .lp-sidebar {
    width: 240px;
  }
}

@media (max-width: 768px) {
  .quick-stats {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .stat-card {
    padding: 14px 16px;
  }

  .stat-value {
    font-size: 20px;
  }

  .mobile-stage-tabs {
    display: flex;
  }

  .lp-sidebar {
    display: none;
  }

  .lp-layout {
    flex-direction: column;
  }

  .hero-banner {
    padding: 24px 20px;
  }

  .hero-title {
    font-size: 20px;
  }

  .hero-meta {
    gap: 12px;
  }

  .path-list-header {
    display: none;
  }

  .path-row {
    flex-wrap: wrap;
    padding: 14px 16px;
    gap: 0;
  }

  .path-row .col-icon { width: 36px; }
  .path-row .col-title { flex: 1; min-width: 0; padding-right: 0; }
  .path-row .col-count { display: none; }
  .path-row .col-hours { display: none; }
  .path-row .col-diff { width: auto; margin-top: 8px; }
  .path-row .col-action { width: auto; margin-top: 8px; margin-left: auto; }

  .lang-icon {
    font-size: 22px;
  }

  .path-name {
    font-size: 14px;
  }

  .path-desc-snippet {
    -webkit-line-clamp: 2;
  }
}
</style>
