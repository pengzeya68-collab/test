<template>
  <div class="exercises">
    <div class="container">
      <!-- 顶部筛选 -->
      <div class="filter-bar">
        <h1 class="page-title">习题库</h1>
        <div class="filters">
          <el-select 
            v-model="currentModule" 
            placeholder="功能模块" 
            style="width: 140px;"
          >
            <el-option label="全部模块" value="" />
            <el-option label="普通习题" value="normal" />
            <el-option label="自动化测试" value="automation" />
            <el-option label="接口测试" value="api" />
          </el-select>
          <el-radio-group v-model="currentStage">
            <el-radio-button :value="1">阶段1</el-radio-button>
            <el-radio-button :value="2">阶段2</el-radio-button>
            <el-radio-button :value="3">阶段3</el-radio-button>
            <el-radio-button :value="4">阶段4</el-radio-button>
            <el-radio-button :value="5">阶段5</el-radio-button>
          </el-radio-group>
          <el-select 
            v-model="currentDifficulty" 
            placeholder="难度筛选" 
            style="width: 120px;"
          >
            <el-option label="全部" value="" />
            <el-option label="简单/初级" value="easy" />
            <el-option label="中等/中级" value="medium" />
            <el-option label="困难/高级" value="hard" />
          </el-select>
          <el-select
            v-model="currentType"
            placeholder="题型筛选"
            style="width: 120px;"
          >
            <el-option label="全部题型" value="" />
            <el-option label="选择题" value="choice" />
            <el-option label="代码题" value="code" />
            <el-option label="SQL题" value="sql" />
            <el-option label="文本题" value="text" />
          </el-select>
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索知识点..." 
            style="width: 200px;"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <!-- 阶段说明 -->
      <div class="stage-info" style="margin-bottom: 30px;">
        <el-alert 
          :title="stageInfo.title" 
          :description="stageInfo.description"
          type="info" 
          show-icon
          :closable="false"
        />
      </div>

      <!-- 习题列表 -->
      <div class="exercises-grid">
        <div
          class="exercise-card"
          :class="{ 'exercise-completed': isExerciseCompleted(exercise.id) }"
          v-for="exercise in paginatedExercises"
          :key="exercise.id"
          @click="goToDetail(exercise.id)"
        >
          <div class="exercise-header">
            <div class="exercise-header-left">
              <span class="completion-badge" v-if="isExerciseCompleted(exercise.id)">✅</span>
              <el-tag :type="getStageTagType(exercise.stage)" size="small">
                阶段{{ exercise.stage }}
              </el-tag>
              <el-tag :type="getDifficultyTagType(exercise.difficulty)" size="small">
                {{ getDifficultyText(exercise.difficulty) }}
              </el-tag>
              <el-tag :type="getExerciseTypeTagType(exercise.exercise_type)" size="small" v-if="exercise.exercise_type">
                {{ getExerciseTypeText(exercise.exercise_type) }}
              </el-tag>
            </div>
            <el-tag v-if="getExerciseScore(exercise.id)" type="success" size="small" effect="dark">
              {{ getExerciseScore(exercise.id) }}分
            </el-tag>
          </div>
          <h3 class="exercise-title">{{ exercise.title }}</h3>
          <p class="exercise-desc">{{ exercise.description }}</p>
          <div class="exercise-meta">
            <div class="meta-item" v-if="exercise.knowledge_point">
              <el-icon size="16"><PriceTag /></el-icon>
              <span class="knowledge-tag">{{ exercise.knowledge_point }}</span>
            </div>
            <div class="meta-item">
              <el-icon size="16"><Timer /></el-icon>
              <span>{{ exercise.time_estimate }}分钟</span>
            </div>
            <div class="meta-item">
              <el-icon size="16"><Collection /></el-icon>
              <span>{{ exercise.category }}</span>
            </div>
          </div>
          <div class="exercise-footer">
            <el-button type="primary" size="small" plain>
              {{ isExerciseCompleted(exercise.id) ? '再做一次' : '开始练习' }}
            </el-button>
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
          :page-sizes="[12, 24, 36, 48]"
          :total="filteredExercises.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Timer, PriceTag, Collection, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const exercises = ref([])
const loading = ref(false)
const currentModule = ref('')
const currentStage = ref(1)
const currentDifficulty = ref('')
const currentType = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const exerciseProgress = ref({})

// 阶段说明
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

// 筛选后的习题列表
const filteredExercises = computed(() => {
  let result = exercises.value
  
  // 按模块筛选
  if (currentModule.value) {
    result = result.filter(item => item.module === currentModule.value)
  }
  
  // 按阶段筛选
  if (currentStage.value > 0) {
    result = result.filter(item => item.stage === currentStage.value)
  }
  
  // 按难度筛选
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
    const typeMap = {
      choice: ['choice', 'multiple_choice', 'true_false'],
      code: ['code'],
      sql: ['sql'],
      text: ['text'],
    }
    const allowedTypes = typeMap[currentType.value] || [currentType.value]
    result = result.filter(item => allowedTypes.includes(item.exercise_type))
  }
  
  // 按关键词搜索
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

// 分页后的习题列表
const paginatedExercises = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredExercises.value.slice(start, end)
})

// 分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

// 页码变化
const handleCurrentChange = (val) => {
  currentPage.value = val
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 模块变化重新获取数据
watch(currentModule, () => {
  currentPage.value = 1
  fetchExercises()
})

// 阶段变化重置页码
watch(currentStage, () => {
  currentPage.value = 1
})

// 难度变化重置页码
watch(currentDifficulty, () => {
  currentPage.value = 1
})

watch(currentType, () => {
  currentPage.value = 1
})

// 搜索关键词变化重置页码
watch(searchKeyword, () => {
  currentPage.value = 1
})

onMounted(() => {
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

const getExerciseScore = (exerciseId) => {
  return exerciseProgress.value[exerciseId]?.score
}

const fetchExercises = async () => {
  loading.value = true
  try {
    // 获取全部习题，后端支持按module筛选
    const params = {
      _t: Date.now() // 添加时间戳防止缓存
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

const getStageTagType = (stage) => {
  const types = ['', 'primary', 'success', 'warning', 'danger', 'info']
  return types[stage] || 'info'
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger',
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger',
  }
  return map[difficulty] || 'info'
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

const getExerciseTypeTagType = (type) => {
  const map = {
    choice: 'primary',
    multiple_choice: 'primary',
    true_false: 'primary',
    code: 'warning',
    sql: 'success',
    text: 'info',
  }
  return map[type] || 'info'
}

const getExerciseTypeText = (type) => {
  const map = {
    choice: '选择题',
    multiple_choice: '多选题',
    true_false: '判断题',
    code: '代码题',
    sql: 'SQL题',
    text: '文本题',
  }
  return map[type] || type
}

const goToDetail = (id) => {
  // 未登录也可以查看习题详情，和代码练习室逻辑一致
  router.push(`/exercises/${id}`)
}
</script>

<style scoped>
.exercises {
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
  gap: 16px;
}

.exercises-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.exercise-card {
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

.exercise-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.exercise-card.exercise-completed {
  border-left: 3px solid rgba(81, 207, 102, 0.6);
  background: rgba(81, 207, 102, 0.03);
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.exercise-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.completion-badge {
  font-size: 16px;
}

.exercise-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin-bottom: 12px;
  line-height: 1.4;
}

.exercise-desc {
  color: var(--tm-text-secondary);
  line-height: 1.7;
  margin-bottom: 20px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  font-size: 14px;
}

.exercise-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--tm-border-light);
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.knowledge-tag {
  background-color: rgba(214, 51, 108, 0.1);
  color: var(--tm-color-primary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.exercise-footer {
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

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 40px;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-title {
    font-size: 24px;
  }

  .exercises-grid {
    grid-template-columns: 1fr;
  }
}
</style>
