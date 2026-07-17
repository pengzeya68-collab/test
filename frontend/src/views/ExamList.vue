<template>
  <div class="exam-list" style="position: relative; z-index: 1;">
    <div class="cyber-grid-bg" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: -1;"></div>
      <div class="page-header">
        <div>
          <h1 class="page-title">鍦ㄧ嚎鑰冭瘯涓績</h1>
          <p class="page-subtitle">妯℃嫙鐪熷疄鑰冭瘯鍦烘櫙锛屾楠屽涔犳垚鏋</p>
        </div>
        <el-button type="primary" @click="openGenerateDialog">
          <el-icon><MagicStick /></el-icon>
          鏅鸿兘缁勫嵎
        </el-button>
      </div>

      <div class="filter-bar">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-select
              v-model="filters.type"
              placeholder="鑰冭瘯绫诲瀷"
              @change="handleFilterChange"
              style="width: 100%;"
              clearable
            >
              <el-option label="妯℃嫙鑰冭瘯" value="妯℃嫙鑰冭瘯" />
              <el-option label="涓撻」缁冧範" value="涓撻」缁冧範" />
              <el-option label="姝ｅ紡鑰冭瘯" value="姝ｅ紡鑰冭瘯" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="filters.difficulty"
              placeholder="闅惧害"
              @change="handleFilterChange"
              style="width: 100%;"
              clearable
            >
              <el-option label="Easy" value="easy" />
              <el-option label="涓瓑" value="medium" />
              <el-option label="鍥伴毦" value="hard" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-input
              v-model="filters.search"
              placeholder="鎼滅储鑰冭瘯鍚嶇О..."
              @keyup.enter="handleFilterChange"
              style="width: 100%;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleFilterChange" style="width: 100%;">
              <el-icon><Search /></el-icon>
              鎼滅储
            </el-button>
          </el-col>
        </el-row>
      </div>

      <div class="exam-grid">
        <div 
          class="exam-card" 
          v-for="exam in exams" 
          :key="exam.id"
        >
          <div class="card-header">
            <div class="exam-title">{{ exam.title }}</div>
            <el-tag :type="getTypeTagType(exam.exam_type)" size="small">
              {{ exam.exam_type }}
            </el-tag>
          </div>
          
          <div class="card-body">
            <p class="exam-desc">{{ exam.description }}</p>
            <div class="exam-info">
              <div class="info-item">
                <el-icon size="14"><Timer /></el-icon>
                <span>{{ exam.duration }}鍒嗛挓</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><Tickets /></el-icon>
                <span>{{ exam.total_score }}鍒</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><List /></el-icon>
                <span>{{ exam.question_count }}棰</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><Star /></el-icon>
                <span>鍙婃牸{{ exam.pass_score }}鍒</span>
              </div>
            </div>
            <div class="difficulty">
              <span>闅惧害锛</span>
              <el-rate 
                v-model="exam.difficultyLevel" 
                disabled 
                :max="3" 
                show-score
                style="font-size: 14px;"
              />
            </div>
          </div>
          
          <div class="card-footer">
            <div class="exam-status" v-if="exam.attempt_status">
              <el-tag :type="exam.is_passed ? 'success' : 'warning'" size="small">
                宸插弬鍔?{{ exam.attempt_score }}鍒?
              </el-tag>
            </div>
            <div class="card-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click="startExam(exam)"
                :disabled="exam.attempt_status === 'submitted'"
              >
                {{ getExamButtonText(exam) }}
              </el-button>
              <el-button 
                type="danger" 
                size="small" 
                @click="deleteExam(exam)"
                :disabled="exam.attempt_status === 'in_progress'"
              >
                <el-icon><Delete /></el-icon>
                鍒犻櫎
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="perPage"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="fetchExams"
        />
      </div>

      <div class="empty-state" v-if="exams.length === 0 && !loading">
        <el-empty description="鏆傛棤鑰冭瘯锛屽揩鏉ョ敓鎴愪綘鐨勪笓灞炶瘯鍗峰惂~" />
      </div>

      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="6" animated />
      </div>

      <!-- 鏅鸿兘缁勫嵎寮圭獥 -->
      <el-dialog 
        v-model="showGenerateDialog" 
        title="鏅鸿兘鐢熸垚璇曞嵎"
        width="600px"
      >
        <el-form :model="generateForm" label-width="100px">
          <el-form-item label="鑰冭瘯绫诲瀷">
            <el-select v-model="generateForm.exam_type" style="width: 200px;">
              <el-option label="妯℃嫙鑰冭瘯" value="妯℃嫙鑰冭瘯" />
              <el-option label="涓撻」缁冧範" value="涓撻」缁冧範" />
            </el-select>
          </el-form-item>
          <el-form-item label="瀛︿範璺緞">
            <el-select 
              v-model="generateForm.learning_path_id" 
              style="width: 360px;"
              placeholder="All learning paths"
              clearable
            >
              <el-option 
                v-for="lp in learningPaths" 
                :key="lp.id" 
                :label="`[闃舵${lp.stage}] ${lp.title}`" 
                :value="lp.id" 
              />
            </el-select>
          </el-form-item>
          <el-form-item label="闅惧害">
            <el-select v-model="generateForm.difficulty" style="width: 200px;">
              <el-option label="Easy" value="easy" />
              <el-option label="涓瓑" value="medium" />
              <el-option label="鍥伴毦" value="hard" />
            </el-select>
          </el-form-item>
          <el-form-item label="鑰冭瘯鏃堕暱">
            <el-input-number 
              v-model="generateForm.duration" 
              :min="30" 
              :max="180" 
              step="10"
              style="width: 200px;"
            />
            <span class="ml-2">鍒嗛挓</span>
          </el-form-item>
          <el-form-item label="棰樺瀷鏁伴噺">
            <el-form-item label="鍗曢€夐" label-width="80px">
              <el-input-number v-model="generateForm.question_count.single_choice" :min="0" :max="50" />
            </el-form-item>
            <el-form-item label="澶氶€夐" label-width="80px">
              <el-input-number v-model="generateForm.question_count.multiple_choice" :min="0" :max="30" />
            </el-form-item>
            <el-form-item label="True or false" label-width="80px">
              <el-input-number v-model="generateForm.question_count.true_false" :min="0" :max="30" />
            </el-form-item>
            <el-form-item label="Code" label-width="80px">
              <el-input-number v-model="generateForm.question_count.code" :min="0" :max="10" />
            </el-form-item>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showGenerateDialog = false">鍙栨秷</el-button>
          <el-button type="primary" @click="generateExam" :loading="generating">鐢熸垚璇曞嵎</el-button>
        </template>
      </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Timer, Tickets, List, Star, Delete, MagicStick 
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const exams = ref([])
const learningPaths = ref([])
const filters = reactive({
  type: '',
  difficulty: '',
  search: ''
})
const currentPage = ref(1)
const perPage = ref(9)
const total = ref(0)
const loading = ref(false)
const showGenerateDialog = ref(false)
const generating = ref(false)

const generateForm = reactive({
  exam_type: '妯℃嫙鑰冭瘯',
  difficulty: 'medium',
  duration: 60,
  learning_path_id: null,
  question_count: {
    single_choice: 10,
    multiple_choice: 5,
    true_false: 5,
    code: 2
  }
})

onMounted(() => {
  fetchExams()
})

const fetchLearningPaths = async () => {
  try {
    const res = await request.get('/learning-paths', { params: { _t: Date.now() } })
    learningPaths.value = Array.isArray(res) ? res : (res.data || res.list || [])
  } catch {}
}

const openGenerateDialog = () => {
  fetchLearningPaths()
  generateForm.learning_path_id = null
  showGenerateDialog.value = true
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchExams()
}

const fetchExams = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: perPage.value,
      type: filters.type,
      difficulty: filters.difficulty,
      search: filters.search.trim()
    }
    
    const res = await request.get('/exams', { params })
    const examList = res.list || res.items || res || []
    exams.value = examList.map(exam => ({
      ...exam,
      difficultyLevel: exam.difficulty === 'easy' ? 1 : exam.difficulty === 'medium' ? 2 : exam.difficulty === 'hard' ? 3 : 2
    }))
    total.value = res.total ?? (Array.isArray(res) ? res.length : 0)
  } catch (error) {
    console.error('鑾峰彇鑰冭瘯鍒楄〃澶辫触:', error)
    ElMessage.error('鑾峰彇鑰冭瘯鍒楄〃澶辫触')
  } finally {
    loading.value = false
  }
}

const getTypeTagType = (type) => {
  const map = {
    '妯℃嫙鑰冭瘯': 'primary',
    '涓撻」缁冧範': 'success',
    '姝ｅ紡鑰冭瘯': 'danger'
  }
  return map[type] || 'info'
}

const getExamButtonText = (exam) => {
  if (exam.attempt_status === 'in_progress') {
    return '缁х画鑰冭瘯'
  } else if (exam.attempt_status) {
    return '鏌ョ湅缁撴灉'
  } else {
    return '寮€濮嬭€冭瘯'
  }
}

const startExam = (exam) => {
  if (exam.attempt_status) {
    if (exam.attempt_status === 'graded' || exam.attempt_status === 'submitted') {
      router.push(`/exam/result/${exam.attempt_id}`)
    } else if (exam.attempt_status === 'in_progress') {
      router.push(`/exam/${exam.id}`)
    } else {
      router.push(`/exam/result/${exam.attempt_id}`)
    }
  } else {
    router.push(`/exam/${exam.id}`)
  }
}

const generateExam = async () => {
  // 检查至少选择一种题型
  const totalQuestions = Object.values(generateForm.question_count).reduce((a, b) => a + b, 0)
  if (totalQuestions === 0) {
    ElMessage.warning('至少选择一种题型')
    return
  }
  
  generating.value = true
  try {
    const res = await request.post('/exams/generate', generateForm)
    ElMessage.success('试卷生成成功')
    showGenerateDialog.value = false
    fetchExams()
    // 跳转到考试页面
    const examId = res.exam_id || res.id || res.data?.exam_id || res.data?.id
    if (examId) {
      router.push(`/exam/${examId}`)
    }
  } catch (error) {
    console.error('生成试卷失败:', error)
    ElMessage.error('生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

const deleteExam = async (exam) => {
  // 姝ｅ湪杩涜鐨勮€冭瘯涓嶈兘鍒犻櫎
  if (exam.attempt_status === 'in_progress') {
    ElMessage.warning('姝ｅ湪杩涜鐨勮€冭瘯涓嶈兘鍒犻櫎')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除考试 "${exam.title}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await request.delete(`/exams/${exam.id}`)
    ElMessage.success('考试删除成功')
    fetchExams()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除考试失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}
</script>

<style scoped>
.exam-list {
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 15px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.page-header :deep(.el-button--primary) {
  background: var(--tm-gradient-brand);
  border: none;
  box-shadow: var(--tm-gradient-brand-glow);
  font-weight: 600;
  padding: 12px 28px;
  border-radius: 12px;
  font-size: 15px;
  animation: breathe 3s ease-in-out infinite;
}

@keyframes breathe {
  0%, 100% { box-shadow: 0 4px 20px rgba(214, 51, 108, 0.4); }
  50% { box-shadow: 0 4px 30px rgba(214, 51, 108, 0.6); }
}

.page-header :deep(.el-button--primary:hover) {
  background: var(--tm-gradient-brand-hover);
  transform: translateY(-2px);
}

.filter-bar {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  padding: 24px;
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  margin-bottom: 32px;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.exam-card {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 16px;
  box-shadow: var(--tm-shadow-card);
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: var(--tm-glass-border);
  display: flex;
  flex-direction: column;
}

.exam-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 16px 24px;
  border-bottom: 1px solid var(--tm-border-light);
}

.exam-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
  line-height: 1.5;
  flex: 1;
  margin-right: 12px;
}

.card-body {
  padding: 20px 24px;
  flex: 1;
}

.exam-desc {
  font-size: 14px;
  color: var(--tm-text-secondary);
  line-height: 1.7;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.exam-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.difficulty {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid var(--tm-border-light);
  background: rgba(255, 255, 255, 0.02);
}

.exam-status {
  display: flex;
  align-items: center;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.pagination-container {
  display: flex;
  justify-content: center;
}

.empty-state, .loading-state {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  padding: 80px 20px;
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
}

.ml-2 {
  margin-left: 8px;
}

@media (max-width: 768px) {
  .exam-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-bar .el-col {
    margin-bottom: 16px;
  }
}
</style>

