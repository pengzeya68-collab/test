<template>
  <div class="exam-list">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">在线考试中心</h1>
          <p class="page-subtitle">模拟真实考试场景，检验学习成果</p>
        </div>
        <el-button type="primary" @click="showGenerateDialog = true">
          <el-icon><MagicStick /></el-icon>
          智能组卷
        </el-button>
      </div>

      <div class="filter-bar">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-select 
              v-model="filters.type" 
              placeholder="考试类型" 
              @change="fetchExams"
              style="width: 100%;"
              clearable
            >
              <el-option label="模拟考试" value="模拟考试" />
              <el-option label="专项练习" value="专项练习" />
              <el-option label="正式考试" value="正式考试" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select 
              v-model="filters.difficulty" 
              placeholder="难度" 
              @change="fetchExams"
              style="width: 100%;"
              clearable
            >
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-input
              v-model="filters.search"
              placeholder="搜索考试名称..."
              @keyup.enter="fetchExams"
              style="width: 100%;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="fetchExams" style="width: 100%;">
              <el-icon><Search /></el-icon>
              搜索
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
                <span>{{ exam.duration }}分钟</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><Tickets /></el-icon>
                <span>{{ exam.total_score }}分</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><List /></el-icon>
                <span>{{ exam.question_count }}题</span>
              </div>
              <div class="info-item">
                <el-icon size="14"><Star /></el-icon>
                <span>及格{{ exam.pass_score }}分</span>
              </div>
            </div>
            <div class="difficulty">
              <span>难度：</span>
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
                已参加 {{ exam.attempt_score }}分
              </el-tag>
            </div>
            <div class="card-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click="startExam(exam)"
                :disabled="exam.attempt_status === 'submitted' || exam.attempt_status === 'graded'"
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
                删除
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
        <el-empty description="暂无考试，快来生成你的专属试卷吧~" />
      </div>

      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="6" animated />
      </div>

      <!-- 智能组卷弹窗 -->
      <el-dialog 
        v-model="showGenerateDialog" 
        title="智能生成试卷"
        width="600px"
      >
        <el-form :model="generateForm" label-width="100px">
          <el-form-item label="考试类型">
            <el-select v-model="generateForm.exam_type" style="width: 200px;">
              <el-option label="模拟考试" value="模拟考试" />
              <el-option label="专项练习" value="专项练习" />
            </el-select>
          </el-form-item>
          <el-form-item label="难度">
            <el-select v-model="generateForm.difficulty" style="width: 200px;">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </el-form-item>
          <el-form-item label="考试时长">
            <el-input-number 
              v-model="generateForm.duration" 
              :min="30" 
              :max="180" 
              step="10"
              style="width: 200px;"
            />
            <span class="ml-2">分钟</span>
          </el-form-item>
          <el-form-item label="题型数量">
            <el-form-item label="单选题" label-width="80px">
              <el-input-number v-model="generateForm.question_count.single_choice" :min="0" :max="50" />
            </el-form-item>
            <el-form-item label="多选题" label-width="80px">
              <el-input-number v-model="generateForm.question_count.multiple_choice" :min="0" :max="30" />
            </el-form-item>
            <el-form-item label="判断题" label-width="80px">
              <el-input-number v-model="generateForm.question_count.true_false" :min="0" :max="30" />
            </el-form-item>
            <el-form-item label="代码题" label-width="80px">
              <el-input-number v-model="generateForm.question_count.code" :min="0" :max="10" />
            </el-form-item>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showGenerateDialog = false">取消</el-button>
          <el-button type="primary" @click="generateExam" :loading="generating">生成试卷</el-button>
        </template>
      </el-dialog>
    </div>
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
  exam_type: '模拟考试',
  difficulty: 'medium',
  duration: 60,
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
    exams.value = res.list.map(exam => ({
      ...exam,
      difficultyLevel: exam.difficulty === 'easy' ? 1 : exam.difficulty === 'medium' ? 2 : 3
    }))
    total.value = res.total
  } catch (error) {
    console.error('获取考试列表失败:', error)
    ElMessage.error('获取考试列表失败')
  } finally {
    loading.value = false
  }
}

const getTypeTagType = (type) => {
  const map = {
    '模拟考试': 'primary',
    '专项练习': 'success',
    '正式考试': 'danger'
  }
  return map[type] || 'info'
}

const getExamButtonText = (exam) => {
  if (exam.attempt_status === 'in_progress') {
    return '继续考试'
  } else if (exam.attempt_status) {
    return '查看结果'
  } else {
    return '开始考试'
  }
}

const startExam = (exam) => {
  if (exam.attempt_status) {
    if (exam.attempt_status === 'graded') {
      router.push(`/exam/result/${exam.attempt_id}`)
    } else {
      router.push(`/exam/${exam.id}`)
    }
  } else {
    router.push(`/exam/${exam.id}`)
  }
}

const generateExam = async () => {
  // 检查至少有一个题型
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
    router.push(`/exam/${res.exam_id}`)
  } catch (error) {
    console.error('生成试卷失败:', error)
    ElMessage.error('生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

const deleteExam = async (exam) => {
  // 正在进行的考试不能删除
  if (exam.attempt_status === 'in_progress') {
    ElMessage.warning('正在进行的考试不能删除')
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
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.filter-bar {
  background: var(--tm-card-bg);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin-bottom: 30px;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  margin-bottom: 30px;
}

.exam-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.exam-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
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
  font-weight: bold;
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
  line-height: 1.6;
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
  color: #606266;
}

.difficulty {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid #f0f2f5;
  background: #fafafa;
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
  background: white;
  padding: 60px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
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
