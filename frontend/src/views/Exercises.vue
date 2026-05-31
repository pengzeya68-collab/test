<template>
  <div class="exercises" style="position: relative; z-index: 1;">
    <div class="cyber-grid-bg" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: -1;"></div>

    <!-- 顶部统计栏 -->
    <div class="stats-bar">
      <div class="stats-bar-inner">
        <div class="stat-item">
          <span class="stat-value">{{ exercises.length }}</span>
          <span class="stat-label">总题数</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value stat-value--success">{{ completedCount }}</span>
          <span class="stat-label">已完成</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value stat-value--accent">{{ accuracyRate }}%</span>
          <span class="stat-label">正确率</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item stat-item--action" v-if="lastUnfinishedExercise">
          <span class="stat-continue" @click="goToDetail(lastUnfinishedExercise.id)">
            <span class="continue-icon">▶</span>
            继续练习：{{ lastUnfinishedExercise.title }}
          </span>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <!-- 题型标签行 -->
      <div class="filter-row">
        <div class="filter-label">题型</div>
        <div class="pill-group">
          <span
            class="pill"
            :class="{ 'pill--active': currentType === '' }"
            @click="currentType = ''"
          >全部</span>
          <span
            class="pill"
            :class="{ 'pill--active': currentType === 'single_choice' }"
            @click="currentType = 'single_choice'"
          >选择题</span>
          <span
            class="pill"
            :class="{ 'pill--active': currentType === 'multiple_choice' }"
            @click="currentType = 'multiple_choice'"
          >多选题</span>
          <span
            class="pill"
            :class="{ 'pill--active': currentType === 'true_false' }"
            @click="currentType = 'true_false'"
          >判断题</span>
          <span
            class="pill"
            :class="{ 'pill--active': currentType === 'code' }"
            @click="currentType = 'code'; currentLanguage = ''"
          >代码题</span>
          <span
            class="pill"
            :class="{ 'pill--active': currentType === 'sql' }"
            @click="currentType = 'code'; currentLanguage = 'sql'"
          >SQL题</span>
        </div>
      </div>

      <!-- 代码语言子分类（选中代码题时显示） -->
      <div class="filter-row" v-if="currentType === 'code'">
        <div class="filter-label">语言</div>
        <div class="pill-group">
          <span
            class="pill pill--lang"
            :class="{ 'pill--active': !currentLanguage }"
            @click="currentLanguage = ''"
          >全部</span>
          <span
            v-for="lang in availableLanguages"
            :key="lang.value"
            class="pill pill--lang"
            :class="{ 'pill--active': currentLanguage === lang.value }"
            @click="currentLanguage = lang.value"
          >{{ lang.label }}</span>
        </div>
      </div>

      <!-- 难度标签行 -->
      <div class="filter-row">
        <div class="filter-label">难度</div>
        <div class="pill-group">
          <span
            class="pill pill--difficulty"
            :class="{ 'pill--active': currentDifficulty === '' }"
            @click="currentDifficulty = ''"
          >全部</span>
          <span
            class="pill pill--difficulty pill--easy"
            :class="{ 'pill--active': currentDifficulty === 'easy' }"
            @click="currentDifficulty = 'easy'"
          >简单</span>
          <span
            class="pill pill--difficulty pill--medium"
            :class="{ 'pill--active': currentDifficulty === 'medium' }"
            @click="currentDifficulty = 'medium'"
          >中等</span>
          <span
            class="pill pill--difficulty pill--hard"
            :class="{ 'pill--active': currentDifficulty === 'hard' }"
            @click="currentDifficulty = 'hard'"
          >困难</span>
        </div>
      </div>

      <!-- 搜索 + 模块 + 阶段 + 随机练习 -->
      <div class="filter-row filter-row--tools">
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索知识点、标题..."
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-select
          v-model="currentModule"
          placeholder="功能模块"
          style="width: 150px;"
          clearable
          filterable
        >
          <el-option label="全部模块" value="" />
          <el-option
            v-for="mod in availableModules"
            :key="mod"
            :label="mod"
            :value="mod"
          />
        </el-select>
        <el-select
          v-model="currentStage"
          placeholder="学习阶段"
          style="width: 130px;"
        >
          <el-option :value="0" label="全部阶段" />
          <el-option :value="1" label="阶段1" />
          <el-option :value="2" label="阶段2" />
          <el-option :value="3" label="阶段3" />
          <el-option :value="4" label="阶段4" />
          <el-option :value="5" label="阶段5" />
        </el-select>
        <button class="random-btn" @click="randomPractice" title="随机练习">
          <span class="random-icon">🎲</span>
          随机练习
        </button>
      </div>
    </div>

    <!-- 阶段说明 -->
    <div class="stage-info" v-if="stageInfo.title">
      <div class="stage-info-inner">
        <span class="stage-info-icon">💡</span>
        <div class="stage-info-content">
          <span class="stage-info-title">{{ stageInfo.title }}</span>
          <span class="stage-info-desc">{{ stageInfo.description }}</span>
        </div>
      </div>
    </div>

    <!-- 习题列表表格 -->
    <div class="exercise-table-wrap" v-if="paginatedExercises.length > 0">
      <div class="exercise-table">
        <!-- 表头 -->
        <div class="exercise-table-header">
          <div class="col col-status">状态</div>
          <div class="col col-id">序号</div>
          <div class="col col-title">题目</div>
          <div class="col col-type">类型</div>
          <div class="col col-difficulty">难度</div>
          <div class="col col-tag">知识点</div>
          <div class="col col-time">时长</div>
          <div class="col col-score">得分</div>
          <div class="col col-action">操作</div>
        </div>
        <!-- 表体 -->
        <div
          class="exercise-row"
          :class="{
            'exercise-row--completed': isExerciseCompleted(exercise.id),
            'exercise-row--wrong': isExerciseWrong(exercise.id),
            'exercise-row--even': (paginatedExercises.indexOf(exercise)) % 2 === 1
          }"
          v-for="exercise in paginatedExercises"
          :key="exercise.id"
          @click="goToDetail(exercise.id)"
        >
          <div class="col col-status">
            <span class="status-icon" v-if="isExerciseCompleted(exercise.id) && !isExerciseWrong(exercise.id)">✅</span>
            <span class="status-icon status-icon--wrong" v-else-if="isExerciseWrong(exercise.id)">❌</span>
            <span class="status-icon status-icon--pending" v-else>⬜</span>
          </div>
          <div class="col col-id">{{ exercise.id }}</div>
          <div class="col col-title" @click="goToDetail(exercise.id)">
            <span class="title-text">{{ exercise.title }}</span>
          </div>
          <div class="col col-type">
            <span class="type-badge" :class="'type-badge--' + exercise.exercise_type" v-if="exercise.exercise_type">
              {{ getExerciseTypeText(exercise.exercise_type) }}
            </span>
          </div>
          <div class="col col-difficulty">
            <span class="diff-badge" :class="'diff-badge--' + exercise.difficulty">
              {{ getDifficultyText(exercise.difficulty) }}
            </span>
          </div>
          <div class="col col-tag">
            <span class="knowledge-tag" v-if="exercise.knowledge_point">{{ exercise.knowledge_point }}</span>
          </div>
          <div class="col col-time">
            <span class="time-text">{{ exercise.time_estimate }}min</span>
          </div>
          <div class="col col-score">
            <span class="score-text" v-if="getExerciseScore(exercise.id)">{{ getExerciseScore(exercise.id) }}分</span>
            <span class="score-text score-text--none" v-else>--</span>
          </div>
          <div class="col col-action">
            <button class="practice-btn" @click.stop="goToDetail(exercise.id)">
              {{ isExerciseCompleted(exercise.id) ? '再做一次' : '开始练习' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="filteredExercises.length === 0 && !loading">
      <el-empty description="暂无符合条件的习题" />
    </div>

    <!-- 加载状态 -->
    <div class="loading" v-if="loading">
      <el-icon class="is-loading" size="40"><Loading /></el-icon>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="paginatedExercises.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[15, 30, 50, 100]"
        :total="filteredExercises.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const exercises = ref([])
const loading = ref(false)
const currentModule = ref('')
const currentStage = ref(0)
const currentDifficulty = ref('')
const currentType = ref('')
const currentLanguage = ref('')
const currentPathId = ref(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(15)
const exerciseProgress = ref({})

const availableModules = computed(() => {
  const modules = new Set()
  exercises.value.forEach(e => {
    if (e.module) modules.add(e.module)
  })
  return [...modules].sort()
})

const availableLanguages = computed(() => {
  const langMap = { python: 'Python', sql: 'SQL', javascript: 'JavaScript', java: 'Java', go: 'Go', rust: 'Rust', c: 'C', cpp: 'C++' }
  const langs = new Set()
  exercises.value.forEach(e => {
    if (e.language && e.exercise_type === 'code') langs.add(e.language)
  })
  return [...langs].map(l => ({ value: l, label: langMap[l] || l.toUpperCase() })).sort((a, b) => a.label.localeCompare(b.label))
})

const completedCount = computed(() => {
  return exercises.value.filter(e => isExerciseCompleted(e.id)).length
})

const accuracyRate = computed(() => {
  const completed = exercises.value.filter(e => isExerciseCompleted(e.id))
  if (completed.length === 0) return 0
  const correct = completed.filter(e => {
    const score = getExerciseScore(e.id)
    return score && score >= 60
  }).length
  return Math.round((correct / completed.length) * 100)
})

const lastUnfinishedExercise = computed(() => {
  return exercises.value.find(e => !isExerciseCompleted(e.id)) || null
})

const stageInfos = {
  1: {
    title: '阶段1 - 测试入门筑基',
    description: '适合零基础入门，掌握软件测试基础理论、测试方法、计算机基础和SQL，为测试生涯打好基础。'
  },
  2: {
    title: '阶段2 - 功能测试精通',
    description: '精通Web/APP/小程序等各类项目的功能测试，掌握完整的测试流程，能独立负责项目测试。'
  },
  3: {
    title: '阶段3 - 测试技术进阶',
    description: '掌握接口测试、Linux、数据库进阶、性能测试基础，成为中级测试工程师。'
  },
  4: {
    title: '阶段4 - 自动化测试专家',
    description: '精通Python编程、接口自动化、UI自动化、APP自动化、性能测试，成为高级自动化测试工程师。'
  },
  5: {
    title: '阶段5 - 测试架构师之路',
    description: '掌握测试平台开发、DevOps、质量体系建设、专项测试技术，向测试架构师/测试专家方向发展。'
  }
}

const stageInfo = computed(() => {
  return stageInfos[currentStage.value] || {}
})

const filteredExercises = computed(() => {
  let result = exercises.value

  if (currentModule.value) {
    result = result.filter(item => item.module === currentModule.value)
  }

  if (currentStage.value > 0) {
    result = result.filter(item => item.stage === currentStage.value || item.stage === null || item.stage === undefined)
  }

  if (currentDifficulty.value) {
    const difficultyMap = {
      easy: ['easy', 'beginner'],
      medium: ['medium', 'intermediate'],
      hard: ['hard', 'advanced'],
    }
    const allowed = difficultyMap[currentDifficulty.value] || [currentDifficulty.value]
    result = result.filter(item => allowed.includes(item.difficulty))
  }

  if (currentType.value) {
    result = result.filter(item => item.exercise_type === currentType.value)
  }

  if (currentLanguage.value) {
    result = result.filter(item => (item.language || '').toLowerCase() === currentLanguage.value.toLowerCase())
  }

  if (currentPathId.value) {
    result = result.filter(item => item.learning_path_id === currentPathId.value)
  }

  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    result = result.filter(item =>
      item.title.toLowerCase().includes(keyword) ||
      (item.description && item.description.toLowerCase().includes(keyword)) ||
      (item.knowledge_point && item.knowledge_point.toLowerCase().includes(keyword))
    )
  }

  return result
})

const paginatedExercises = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredExercises.value.slice(start, end)
})

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(currentModule, () => {
  currentPage.value = 1
  fetchExercises()
})

watch(currentStage, () => {
  currentPage.value = 1
})

watch(currentDifficulty, () => {
  currentPage.value = 1
})

watch(currentType, () => {
  currentPage.value = 1
})

watch(searchKeyword, () => {
  currentPage.value = 1
})

onMounted(() => {
  const pathIdParam = route.query.pathId
  if (pathIdParam) {
    currentPathId.value = Number(pathIdParam)
    currentStage.value = 0
  }
  fetchExercises()
  if (userStore.isLoggedIn) {
    fetchProgress()
  }
})

const fetchProgress = async () => {
  try {
    const res = await request.get('/exercise/progress')
    exerciseProgress.value = res.progress || {}
  } catch (error) {
    console.error('获取习题进度失败:', error)
  }
}

const isExerciseCompleted = (exerciseId) => {
  return exerciseProgress.value[exerciseId]?.completed || false
}

const isExerciseWrong = (exerciseId) => {
  const progress = exerciseProgress.value[exerciseId]
  return progress?.completed && progress?.score !== undefined && progress.score < 60
}

const getExerciseScore = (exerciseId) => {
  return exerciseProgress.value[exerciseId]?.score
}

const fetchExercises = async () => {
  loading.value = true
  try {
    const params = {
      _t: Date.now()
    }
    if (currentModule.value) {
      params.module = currentModule.value
    }
    const res = await request.get('/exercises', { params })
    if (Array.isArray(res.data)) {
      exercises.value = res.data
    } else if (Array.isArray(res)) {
      exercises.value = res
    } else {
      exercises.value = []
    }
  } catch (error) {
    console.error('获取习题列表失败:', error)
    ElMessage.error('获取习题列表失败')
  } finally {
    loading.value = false
  }
}

const getDifficultyText = (difficulty) => {
  const map = {
    easy: '简单',
    medium: '中等',
    hard: '困难',
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级',
  }
  return map[difficulty] || difficulty
}

const getExerciseTypeText = (type) => {
  const map = {
    choice: '选择题',
    single_choice: '选择题',
    multiple_choice: '多选题',
    true_false: '判断题',
    code: '代码题',
    sql: 'SQL题',
    text: '文本题',
  }
  return map[type] || type
}

const goToDetail = (id) => {
  router.push(`/exercises/${id}`)
}

const randomPractice = () => {
  const unfinished = exercises.value.filter(e => !isExerciseCompleted(e.id))
  if (unfinished.length === 0) {
    ElMessage.info('所有习题已完成，太厉害了！')
    return
  }
  const random = unfinished[Math.floor(Math.random() * unfinished.length)]
  goToDetail(random.id)
}
</script>

<style scoped>
.exercises {
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

/* ========== 顶部统计栏 ========== */
.stats-bar {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border: var(--tm-glass-border);
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 20px;
  box-shadow: var(--tm-shadow-card);
}

.stats-bar-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 80px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--tm-text-primary);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.stat-value--success {
  color: var(--tm-color-success, #4ADE80);
}

.stat-value--accent {
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
  letter-spacing: 0.5px;
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: var(--tm-border-light);
}

.stat-item--action {
  margin-left: auto;
}

.stat-continue {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--tm-color-primary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 18px;
  border-radius: 20px;
  background: rgba(236, 72, 153, 0.08);
  border: 1px solid rgba(236, 72, 153, 0.2);
  transition: all 0.3s ease;
  white-space: nowrap;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-continue:hover {
  background: rgba(236, 72, 153, 0.15);
  border-color: rgba(236, 72, 153, 0.4);
  box-shadow: 0 0 12px rgba(236, 72, 153, 0.2);
}

.continue-icon {
  font-size: 12px;
}

/* ========== 筛选区域 ========== */
.filter-section {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border: var(--tm-glass-border);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: var(--tm-shadow-card);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
  min-width: 36px;
  flex-shrink: 0;
  font-weight: 500;
}

.pill-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  color: var(--tm-text-regular);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.25s ease;
  user-select: none;
  white-space: nowrap;
}

.pill:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  color: var(--tm-text-primary);
}

.pill--active {
  background: rgba(236, 72, 153, 0.12);
  border-color: rgba(236, 72, 153, 0.3);
  color: var(--tm-color-primary);
  font-weight: 500;
}

.pill--active:hover {
  background: rgba(236, 72, 153, 0.18);
  border-color: rgba(236, 72, 153, 0.4);
}

.pill--easy.pill--active {
  background: rgba(74, 222, 128, 0.1);
  border-color: rgba(74, 222, 128, 0.3);
  color: #4ADE80;
}

.pill--medium.pill--active {
  background: rgba(250, 204, 21, 0.1);
  border-color: rgba(250, 204, 21, 0.3);
  color: #FACC15;
}

.pill--hard.pill--active {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.3);
  color: #F87171;
}

.pill--lang.pill--active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
  border-color: rgba(139, 92, 246, 0.4);
  color: #A78BFA;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.15);
}

.filter-row--tools {
  margin-top: 4px;
  padding-top: 14px;
  border-top: 1px solid var(--tm-border-light);
}

.search-box {
  flex: 1;
  max-width: 320px;
}

.random-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  color: var(--tm-color-primary);
  background: rgba(236, 72, 153, 0.08);
  border: 1px solid rgba(236, 72, 153, 0.2);
  transition: all 0.3s ease;
  white-space: nowrap;
  margin-left: auto;
  font-weight: 500;
}

.random-btn:hover {
  background: rgba(236, 72, 153, 0.15);
  border-color: rgba(236, 72, 153, 0.4);
  box-shadow: 0 0 12px rgba(236, 72, 153, 0.2);
}

.random-icon {
  font-size: 15px;
}

/* ========== 阶段说明 ========== */
.stage-info {
  margin-bottom: 20px;
}

.stage-info-inner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  background: rgba(236, 72, 153, 0.04);
  border: 1px solid rgba(236, 72, 153, 0.12);
  border-radius: 12px;
}

.stage-info-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.stage-info-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stage-info-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.stage-info-desc {
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
}

/* ========== 习题表格 ========== */
.exercise-table-wrap {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border: var(--tm-glass-border);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--tm-shadow-card);
}

.exercise-table {
  width: 100%;
}

.exercise-table-header {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--tm-border-light);
  font-size: 12px;
  font-weight: 600;
  color: var(--tm-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.exercise-row {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
  transition: all 0.2s ease;
  cursor: pointer;
}

.exercise-row:last-child {
  border-bottom: none;
}

.exercise-row--even {
  background: rgba(255, 255, 255, 0.015);
}

.exercise-row:hover {
  background: rgba(236, 72, 153, 0.04);
}

.exercise-row--completed {
  border-left: 3px solid rgba(74, 222, 128, 0.5);
}

.exercise-row--wrong {
  border-left: 3px solid rgba(248, 113, 113, 0.5);
}

/* 列宽定义 */
.col {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.col-status {
  width: 44px;
  justify-content: center;
}

.col-id {
  width: 52px;
  font-size: 13px;
  color: var(--tm-text-secondary);
  font-variant-numeric: tabular-nums;
}

.col-title {
  flex: 1;
  min-width: 0;
}

.col-type {
  width: 72px;
  justify-content: center;
}

.col-difficulty {
  width: 60px;
  justify-content: center;
}

.col-tag {
  width: 120px;
  justify-content: center;
}

.col-time {
  width: 56px;
  justify-content: center;
}

.col-score {
  width: 56px;
  justify-content: center;
}

.col-action {
  width: 100px;
  justify-content: flex-end;
}

/* 状态图标 */
.status-icon {
  font-size: 16px;
  line-height: 1;
}

.status-icon--wrong {
  font-size: 14px;
}

.status-icon--pending {
  font-size: 14px;
  opacity: 0.4;
}

/* 标题 */
.title-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
  cursor: pointer;
  transition: color 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-text:hover {
  color: var(--tm-color-primary);
}

/* 类型徽章 */
.type-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.type-badge--single_choice,
.type-badge--choice {
  background: rgba(96, 165, 250, 0.1);
  color: #60A5FA;
  border: 1px solid rgba(96, 165, 250, 0.2);
}

.type-badge--multiple_choice {
  background: rgba(167, 139, 250, 0.1);
  color: #A78BFA;
  border: 1px solid rgba(167, 139, 250, 0.2);
}

.type-badge--true_false {
  background: rgba(45, 212, 191, 0.1);
  color: #2DD4BF;
  border: 1px solid rgba(45, 212, 191, 0.2);
}

.type-badge--code {
  background: rgba(251, 191, 36, 0.1);
  color: #FBBF24;
  border: 1px solid rgba(251, 191, 36, 0.2);
}

.type-badge--sql {
  background: rgba(74, 222, 128, 0.1);
  color: #4ADE80;
  border: 1px solid rgba(74, 222, 128, 0.2);
}

.type-badge--text {
  background: rgba(161, 161, 170, 0.1);
  color: #A1A1AA;
  border: 1px solid rgba(161, 161, 170, 0.2);
}

/* 难度徽章 */
.diff-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.diff-badge--easy,
.diff-badge--beginner {
  background: rgba(74, 222, 128, 0.1);
  color: #4ADE80;
  border: 1px solid rgba(74, 222, 128, 0.2);
}

.diff-badge--medium,
.diff-badge--intermediate {
  background: rgba(250, 204, 21, 0.1);
  color: #FACC15;
  border: 1px solid rgba(250, 204, 21, 0.2);
}

.diff-badge--hard,
.diff-badge--advanced {
  background: rgba(248, 113, 113, 0.1);
  color: #F87171;
  border: 1px solid rgba(248, 113, 113, 0.2);
}

/* 知识点标签 */
.knowledge-tag {
  display: inline-block;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: rgba(236, 72, 153, 0.08);
  color: var(--tm-color-primary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

/* 时长 */
.time-text {
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-variant-numeric: tabular-nums;
}

/* 得分 */
.score-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--tm-color-success, #4ADE80);
  font-variant-numeric: tabular-nums;
}

.score-text--none {
  color: var(--tm-text-secondary);
  font-weight: 400;
  opacity: 0.4;
}

/* 练习按钮 */
.practice-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  color: #fff;
  background: var(--tm-gradient-brand);
  border: none;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.practice-btn:hover {
  box-shadow: 0 0 14px rgba(236, 72, 153, 0.35);
  transform: translateY(-1px);
}

/* ========== 空状态 & 加载 ========== */
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

/* ========== 分页 ========== */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 28px;
  padding: 20px 0;
}

/* ========== 响应式 ========== */
@media (max-width: 1024px) {
  .col-tag {
    display: none;
  }
  .col-time {
    display: none;
  }
}

@media (max-width: 768px) {
  .stats-bar-inner {
    gap: 16px;
  }
  .stat-value {
    font-size: 22px;
  }
  .stat-item--action {
    margin-left: 0;
    width: 100%;
  }
  .stat-continue {
    width: 100%;
    max-width: none;
  }
  .filter-row {
    flex-wrap: wrap;
  }
  .filter-label {
    min-width: auto;
  }
  .search-box {
    max-width: none;
    width: 100%;
  }
  .filter-row--tools {
    flex-wrap: wrap;
  }
  .random-btn {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
  .col-id,
  .col-score {
    display: none;
  }
  .col-type {
    width: 60px;
  }
  .col-difficulty {
    width: 50px;
  }
  .col-action {
    width: 80px;
  }
  .exercise-table-header {
    padding: 12px 14px;
  }
  .exercise-row {
    padding: 12px 14px;
  }
}
</style>
