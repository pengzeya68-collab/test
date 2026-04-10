<template>
  <div class="interview-simulate">
    <div class="container">
      <div class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </div>

      <div class="setup-card" v-if="!sessionId">
        <h2 class="card-title">创建模拟面试</h2>
        <el-form :model="form" label-width="120px">
          <el-form-item label="应聘岗位">
            <el-input v-model="form.position" placeholder="例如：测试工程师" />
          </el-form-item>
          <el-form-item label="岗位级别">
            <el-select v-model="form.level" style="width: 200px;">
              <el-option label="初级" value="初级" />
              <el-option label="中级" value="中级" />
              <el-option label="高级" value="高级" />
              <el-option label="专家" value="专家" />
            </el-select>
          </el-form-item>
          <el-form-item label="面试类型">
            <el-select v-model="form.type" style="width: 200px;">
              <el-option label="技术面试" value="技术面" />
              <el-option label="HR面试" value="HR面" />
              <el-option label="综合面试" value="综合面" />
            </el-select>
          </el-form-item>
          <el-form-item label="题目数量">
            <el-input-number v-model="form.question_count" :min="5" :max="20" />
          </el-form-item>
          <el-form-item label="考察范围">
            <el-checkbox-group v-model="form.categories">
              <el-checkbox 
                v-for="cat in categories" 
                :key="cat.value" 
                :label="cat.value"
              >
                {{ cat.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="createSession" :loading="creating">
              开始面试
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="interview-card" v-if="sessionId && session && questions.length > 0">
        <div class="interview-header">
          <div class="interview-info">
            <h2>{{ session.title }}</h2>
            <div class="interview-progress">
              <span>第 {{ currentQuestionIndex + 1 }} 题 / 共 {{ questions.length }} 题</span>
              <el-progress 
                :percentage="Math.round((currentQuestionIndex + 1) / questions.length * 100)" 
                :show-text="false"
                style="width: 200px; margin-left: 16px;"
              />
            </div>
          </div>
          <div class="interview-actions">
            <el-button type="danger" @click="showCompleteConfirm = true">
              结束面试
            </el-button>
          </div>
        </div>

        <div class="question-section" v-if="currentQuestion">
          <div class="question-header">
            <div class="question-meta">
              <el-tag size="small" type="primary">{{ currentQuestion.category }}</el-tag>
              <el-tag size="small" :type="getDifficultyTagType(currentQuestion.difficulty)">
                {{ currentQuestion.difficulty === 'easy' ? '简单' : currentQuestion.difficulty === 'medium' ? '中等' : '困难' }}
              </el-tag>
            </div>
          </div>
          
          <div class="question-content">
            <h3>{{ currentQuestion.title }}</h3>
            <div v-if="currentQuestion.content" class="question-desc" v-html="renderMarkdown(currentQuestion.content)"></div>
          </div>

          <div class="answer-section">
            <div class="answer-header">
              <h4>你的回答</h4>
              <el-button 
                type="text" 
                @click="showAnswerHint = !showAnswerHint"
                :style="{ color: showAnswerHint ? '#e6a23c' : '#909399' }"
              >
                {{ showAnswerHint ? '隐藏提示' : '提示一下' }}
              </el-button>
            </div>
            
            <div class="hint-box" v-if="showAnswerHint">
              <el-alert
                title="答题提示"
                type="warning"
                :closable="false"
                show-icon
              >
                <template #default>
                  请尽量详细地回答问题，体现你的思考过程。回答完成后点击提交按钮，AI会自动为你评分和点评。
                </template>
              </el-alert>
            </div>
            
            <el-input
              v-model="currentAnswer"
              type="textarea"
              :rows="8"
              placeholder="请输入你的回答..."
              maxlength="5000"
              show-word-limit
            />
            
            <!-- AI点评结果 -->
            <div class="feedback-section" v-if="currentQuestion.is_answered">
              <el-divider content-position="left">AI点评</el-divider>
              <div class="score-display">
                <span>得分：</span>
                <el-rate 
                  v-model="currentQuestion.score" 
                  disabled 
                  :max="10" 
                  show-score
                  style="font-size: 20px;"
                />
                <span class="score-text">/ 10分</span>
              </div>
              <div class="feedback-content">
                <p>{{ currentQuestion.ai_feedback }}</p>
              </div>
              
              <el-collapse>
                <el-collapse-item title="查看参考答案">
                  <div v-html="renderMarkdown(currentQuestion.answer)"></div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>

          <div class="action-buttons">
            <el-button 
              :disabled="currentQuestionIndex === 0"
              @click="prevQuestion"
            >
              上一题
            </el-button>
            <el-button 
              v-if="!currentQuestion.is_answered"
              type="primary" 
              @click="submitAnswer"
              :loading="submitting"
            >
              提交回答
            </el-button>
            <el-button 
              v-else
              type="primary" 
              :disabled="currentQuestionIndex === questions.length - 1"
              @click="nextQuestion"
            >
              下一题
            </el-button>
          </div>
        </div>
      </div>

      <!-- 面试结果弹窗 -->
      <el-dialog 
        v-model="showResultDialog" 
        title="面试结束"
        width="700px"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
      >
        <div v-if="result" class="result-content">
          <div class="result-score">
            <div class="score-circle" :class="result.score >= 60 ? 'passed' : 'failed'">
              <div class="score-number">{{ result.score }}</div>
              <div class="score-label">分</div>
            </div>
            <div class="score-info">
              <h3>面试评分</h3>
              <p>{{ result.feedback }}</p>
            </div>
          </div>
          
          <div class="suggestions-section">
            <h4>改进建议</h4>
            <div class="suggestions-content">
              <p v-html="renderMarkdown(result.suggestions)"></p>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button @click="goToDetail">查看详情</el-button>
          <el-button type="primary" @click="restart">再来一次</el-button>
        </template>
      </el-dialog>

      <!-- 结束面试确认弹窗 -->
      <el-dialog 
        v-model="showCompleteConfirm" 
        title="确认结束面试"
        width="400px"
      >
        <p>你确定要结束本次面试吗？结束后将无法继续答题。</p>
        <template #footer>
          <el-button @click="showCompleteConfirm = false">取消</el-button>
          <el-button type="danger" @click="completeInterview" :loading="completing">确认结束</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, VideoPlay, Star 
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'

const router = useRouter()

const form = reactive({
  position: '测试工程师',
  level: '中级',
  type: '技术面',
  question_count: 10,
  categories: []
})

const categories = ref([])
const creating = ref(false)
const sessionId = ref(null)
const session = ref(null)
const questions = ref([])
const currentQuestionIndex = ref(0)
const currentAnswer = ref('')
const showAnswerHint = ref(false)
const submitting = ref(false)
const completing = ref(false)
const showResultDialog = ref(false)
const showCompleteConfirm = ref(false)
const result = ref(null)

const currentQuestion = computed(() => {
  return questions.value[currentQuestionIndex.value]
})

onMounted(() => {
  fetchCategories()
})

const fetchCategories = async () => {
  try {
    const res = await request.get('/interview/categories')
    categories.value = res
    // 默认选中所有技术类分类
    form.categories = res.filter(c => c.value !== 'HR面' && c.value !== '职业规划').map(c => c.value)
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const createSession = async () => {
  if (form.categories.length === 0) {
    ElMessage.warning('请至少选择一个考察范围')
    return
  }
  
  creating.value = true
  try {
    const res = await request.post('/interview/sessions/create', form)
    sessionId.value = res.session_id
    await fetchSession()
    ElMessage.success('面试会话创建成功，开始面试吧！')
  } catch (error) {
    console.error('创建面试会话失败:', error)
    ElMessage.error('创建失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const fetchSession = async () => {
  try {
    const res = await request.get(`/interview/sessions/${sessionId.value}`)
    session.value = res.session
    questions.value = res.questions
    
    // 初始化当前题目的答案
    if (questions.value.length > 0) {
      currentAnswer.value = questions.value[0].user_answer || ''
    }
  } catch (error) {
    console.error('获取面试会话失败:', error)
    ElMessage.error('获取面试信息失败')
  }
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    'easy': 'success',
    'medium': 'warning',
    'hard': 'danger'
  }
  return map[difficulty] || 'info'
}

const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    // 保存当前答案
    if (currentQuestion.value) {
      currentQuestion.value.user_answer = currentAnswer.value
    }
    
    currentQuestionIndex.value -= 1
    currentAnswer.value = questions.value[currentQuestionIndex.value].user_answer || ''
  }
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < questions.value.length - 1) {
    // 保存当前答案
    if (currentQuestion.value) {
      currentQuestion.value.user_answer = currentAnswer.value
    }
    
    currentQuestionIndex.value += 1
    currentAnswer.value = questions.value[currentQuestionIndex.value].user_answer || ''
    showAnswerHint.value = false
  }
}

const submitAnswer = async () => {
  if (!currentAnswer.value.trim()) {
    ElMessage.warning('请输入你的回答')
    return
  }
  
  submitting.value = true
  try {
    const res = await request.post(`/interview/sessions/${sessionId.value}/submit-answer`, {
      record_id: currentQuestion.value.record_id,
      answer: currentAnswer.value.trim()
    })
    
    // 更新题目状态
    currentQuestion.value.is_answered = true
    currentQuestion.value.score = res.score
    currentQuestion.value.ai_feedback = res.feedback
    currentQuestion.value.answer = res.correct_answer
    
    ElMessage.success('回答提交成功！')
  } catch (error) {
    console.error('提交答案失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const completeInterview = async () => {
  completing.value = true
  try {
    const res = await request.post(`/interview/sessions/${sessionId.value}/complete`)
    result.value = res
    showResultDialog.value = true
    showCompleteConfirm.value = false
  } catch (error) {
    console.error('结束面试失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    completing.value = false
  }
}

const goToDetail = () => {
  router.push(`/interview/detail/${sessionId.value}`)
}

const restart = () => {
  // 重置状态
  sessionId.value = null
  session.value = null
  questions.value = []
  currentQuestionIndex.value = 0
  currentAnswer.value = ''
  showAnswerHint.value = false
  showResultDialog.value = false
  result.value = null
}

const renderMarkdown = (content) => {
  return marked(content || '')
}
</script>

<style scoped>
.interview-simulate {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--tm-card-bg);
  border-radius: 8px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: var(--tm-text-secondary);
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.back-btn:hover {
  color: var(--tm-color-primary);
  transform: translateX(-4px);
}

.setup-card, .interview-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.card-title {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 30px 0;
  text-align: center;
}

.interview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--tm-border-light);
}

.interview-info h2 {
  font-size: 20px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.interview-progress {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--tm-text-secondary);
}

.question-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.question-header {
  margin-bottom: 16px;
}

.question-content h3 {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
  line-height: 1.8;
  margin: 0 0 16px 0;
}

.question-desc {
  font-size: 15px;
  line-height: 2;
  color: var(--tm-text-secondary);
  padding: 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 8px;
  border-left: 4px solid var(--tm-border-light);
}

.answer-section {
  margin-top: 20px;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.answer-header h4 {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0;
}

.hint-box {
  margin-bottom: 16px;
}

.feedback-section {
  margin-top: 24px;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 500;
  color: var(--tm-text-primary);
}

.score-text {
  color: var(--tm-text-secondary);
  font-weight: normal;
}

.feedback-content {
  padding: 16px;
  background: rgba(var(--tm-color-primary), 0.1);
  border-radius: 8px;
  border-left: 4px solid var(--tm-color-primary);
  margin-bottom: 16px;
}

.feedback-content p {
  margin: 0;
  line-height: 1.8;
  color: var(--tm-text-primary);
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--tm-border-light);
  padding-top: 24px;
  margin-top: 24px;
}

/* 结果弹窗样式 */
.result-content {
  padding: 20px 0;
}

.result-score {
  display: flex;
  align-items: center;
  gap: 40px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--tm-border-light);
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-circle.passed {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.score-circle.failed {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.score-number {
  font-size: 36px;
  font-weight: bold;
  color: white;
  line-height: 1;
  margin-bottom: 4px;
}

.score-label {
  font-size: 14px;
  color: white;
  opacity: 0.9;
}

.score-info h3 {
  font-size: 20px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.score-info p {
  font-size: 15px;
  line-height: 1.8;
  color: var(--tm-text-secondary);
  margin: 0;
}

.suggestions-section h4 {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 16px 0;
}

.suggestions-content {
  padding: 20px;
  background: rgba(230, 162, 60, 0.1);
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
}

.suggestions-content p {
  margin: 0;
  line-height: 2;
  color: var(--tm-text-primary);
  white-space: pre-line;
}

/* Markdown样式 */
.question-desc, .feedback-content, .suggestions-content {
  line-height: 2;
}

.question-desc p, .feedback-content p, .suggestions-content p {
  margin: 12px 0;
  color: var(--tm-text-primary);
}

.question-desc ul,
.question-desc ol,
.feedback-content ul,
.feedback-content ol {
  margin: 12px 0;
  padding-left: 24px;
  color: var(--tm-text-primary);
}

.question-desc li,
.feedback-content li {
  margin: 8px 0;
  color: var(--tm-text-primary);
}

.question-desc code,
.feedback-content code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
}

@media (max-width: 768px) {
  .setup-card, .interview-card {
    padding: 20px;
  }

  .interview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .result-score {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
}
</style>
