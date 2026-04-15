﻿<template>
  <div class="exam-page">
    <div class="exam-header">
      <div class="container">
        <div class="header-content">
          <div class="exam-info">
            <h1 class="exam-title">{{ exam?.title }}</h1>
            <div class="exam-meta">
              <span>总分：{{ exam?.total_score }}分</span>
              <span>及格：{{ exam?.pass_score }}分</span>
              <span>题目数：{{ questions.length }}题</span>
            </div>
          </div>
          <div class="timer">
            <div class="time-left">
              <el-icon size="20"><Timer /></el-icon>
              <span class="time-text">{{ formatTime(remainingTime) }}</span>
            </div>
            <el-progress 
              :percentage="timePercentage" 
              :color="timeProgressColor"
              :show-text="false"
              stroke-width="6"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="exam-container">
        <!-- 左侧题目导航 -->
        <div class="question-nav">
          <div class="nav-header">题目导航</div>
          <div class="nav-grid">
            <div 
              class="nav-item" 
              v-for="(q, index) in questions" 
              :key="q.id"
              :class="{ 
                active: currentQuestionIndex === index,
                answered: userAnswers[q.id] !== undefined && userAnswers[q.id] !== '',
                marked: markedQuestions.includes(q.id)
              }"
              @click="jumpToQuestion(index)"
            >
              {{ index + 1 }}
            </div>
          </div>
          <div class="nav-legend">
            <div class="legend-item">
              <span class="legend-dot answered"></span>
              <span>已答</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot"></span>
              <span>未答</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot marked"></span>
              <span>标记</span>
            </div>
          </div>
        </div>

        <!-- 中间题目内容 -->
        <div class="question-content" v-if="currentQuestion">
          <div class="question-header">
            <div class="question-number">第 {{ currentQuestionIndex + 1 }} 题 ({{ currentQuestion.score }}分)</div>
            <el-button 
              link 
              :icon="markedQuestions.includes(currentQuestion.id) ? StarFilled : Star"
              @click="toggleMarkQuestion"
              :style="{ color: markedQuestions.includes(currentQuestion.id) ? '#e6a23c' : 'var(--tm-text-secondary)' }"
            >
              {{ markedQuestions.includes(currentQuestion.id) ? '已标记' : '标记此题' }}
            </el-button>
          </div>
          
          <div class="question-body">
            <div class="question-type">
              <el-tag size="small" type="info">
                {{ getQuestionTypeText(currentQuestion.question_type) }}
              </el-tag>
            </div>
            <div class="question-text" v-html="renderMarkdown(currentQuestion.content)"></div>
            
            <!-- 单选题 -->
            <div v-if="currentQuestion.question_type === 'single_choice'" class="options">
              <el-radio-group v-model="userAnswers[currentQuestion.id]">
                <el-radio 
                  :value="String.fromCharCode(65 + index)"
                  v-for="(option, index) in currentQuestion.options" 
                  :key="`${currentQuestion.id}-opt-${index}`"
                >
                  {{ String.fromCharCode(65 + index) }}. {{ option }}
                </el-radio>
              </el-radio-group>
            </div>
            
            <!-- 多选题 -->
            <div v-if="currentQuestion.question_type === 'multiple_choice'" class="options">
              <el-checkbox-group 
                v-model="selectedOptions" 
                @change="updateMultipleChoiceAnswer"
              >
                <el-checkbox 
                  :value="String.fromCharCode(65 + index)"
                  v-for="(option, index) in currentQuestion.options" 
                  :key="`${currentQuestion.id}-opt-${index}`"
                >
                  {{ String.fromCharCode(65 + index) }}. {{ option }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
            
            <!-- 判断题 -->
            <div v-if="currentQuestion.question_type === 'true_false'" class="options">
              <el-radio-group v-model="userAnswers[currentQuestion.id]">
                <el-radio value="true">正确</el-radio>
                <el-radio value="false">错误</el-radio>
              </el-radio-group>
            </div>
            
            <!-- 简答题 -->
            <div v-if="currentQuestion.question_type === 'short_answer'" class="answer-area">
              <el-input
                v-model="userAnswers[currentQuestion.id]"
                type="textarea"
                :rows="6"
                placeholder="请输入你的答案..."
                maxlength="2000"
                show-word-limit
              />
            </div>
            
            <!-- 代码题 -->
            <div v-if="currentQuestion.question_type === 'code'" class="answer-area">
              <CodeEditor 
                v-model="userAnswers[currentQuestion.id]"
                :language="exam?.language || 'python'"
                height="300px"
              />
            </div>
          </div>
          
          <div class="question-actions">
            <el-button 
              :disabled="currentQuestionIndex === 0"
              @click="prevQuestion"
            >
              上一题
            </el-button>
            <el-button 
              type="primary" 
              :disabled="currentQuestionIndex === questions.length - 1"
              @click="nextQuestion"
            >
              下一题
            </el-button>
          </div>
        </div>
      </div>

      <!-- 底部提交栏 -->
      <div class="submit-bar">
        <div class="container">
          <div class="submit-info">
            <div class="info-item">
              <span class="label">已答</span>
              <span class="value answered">{{ answeredCount }}</span>
              <span class="total">/ {{ questions.length }}</span>
            </div>
            <div class="divider"></div>
            <div class="info-item">
              <span class="label">未答</span>
              <span class="value unanswered">{{ questions.length - answeredCount }}</span>
            </div>
            <div class="divider"></div>
            <div class="info-item">
              <span class="label">标记</span>
              <span class="value marked">{{ markedQuestions.length }}</span>
            </div>
          </div>
          <div class="submit-actions">
            <el-button 
              type="warning" 
              size="large"
              @click="jumpToMarkedQuestion"
              v-if="markedQuestions.length > 0"
              class="marked-btn"
            >
              <el-icon><Collection /></el-icon>
              查看标记
            </el-button>
            <el-button 
              type="danger" 
              size="large"
              @click="showSubmitConfirm = true"
              class="submit-btn"
            >
              <el-icon><CircleCheck /></el-icon>
              交卷
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 提交确认弹窗 -->
    <el-dialog 
      v-model="showSubmitConfirm" 
      title="确认交卷"
      width="500px"
    >
      <p>你确定要提交考试吗？提交后将无法修改答案。</p>
      <p>当前已答 {{ answeredCount }} 题，还有 {{ questions.length - answeredCount }} 题未答。</p>
      <template #footer>
        <el-button @click="showSubmitConfirm = false">取消</el-button>
        <el-button type="danger" @click="submitExam" :loading="submitting">确认交卷</el-button>
      </template>
    </el-dialog>

    <!-- 时间提醒弹窗 -->
    <el-dialog 
      v-model="showTimeWarning" 
      title="时间提醒"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <p>距离考试结束还有 <strong>{{ remainingTime }}分钟</strong>，请合理安排时间。</p>
      <template #footer>
        <el-button type="primary" @click="showTimeWarning = false">知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Timer, Star, StarFilled, CircleCheck, Collection } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { renderMarkdown } from '@/utils/markdown'
import CodeEditor from '@/components/CodeEditor.vue'

const router = useRouter()
const route = useRoute()
const examId = route.params.id

const exam = ref(null)
const questions = ref([])
const attemptId = ref(null)
const currentQuestionIndex = ref(0)
const userAnswers = ref({})
const selectedOptions = ref([])
const markedQuestions = ref([])
const remainingTime = ref(0)
let examTimer = null
const showSubmitConfirm = ref(false)
const showTimeWarning = ref(false)
const submitting = ref(false)

const currentQuestion = computed(() => {
  return questions.value[currentQuestionIndex.value]
})

const answeredCount = computed(() => {
  return Object.values(userAnswers.value).filter(v => v !== undefined && v !== '').length
})

const timePercentage = computed(() => {
  if (!exam.value) return 0
  return Math.round((exam.value.duration - remainingTime.value) / exam.value.duration * 100)
})

const timeProgressColor = computed(() => {
  if (remainingTime.value <= 10) return '#f56c6c'
  if (remainingTime.value <= 30) return '#e6a23c'
  return '#67c23a'
})

onMounted(() => {
  fetchExamQuestions()
})

onBeforeUnmount(() => {
  if (examTimer) {
    clearInterval(examTimer)
    examTimer = null
  }
})

const fetchExamQuestions = async () => {
  try {
    const res = await request.get(`/exams/${examId}/questions`)
    exam.value = res.exam
    questions.value = res.questions
    attemptId.value = res.attempt_id
    
    // 初始化倒计时
    remainingTime.value = exam.value.duration
    startTimer()
    
    // 初始化用户答案
    questions.value.forEach(q => {
      userAnswers.value[q.id] = ''
    })
    
    // 如果是多选题，初始化选项数组
    if (currentQuestion.value?.question_type === 'multiple_choice') {
      selectedOptions.value = []
    }
    
  } catch (error) {
    console.error('获取考试题目失败:', error)
    ElMessage.error('获取考试题目失败')
    router.back()
  }
}

const startTimer = () => {
  // 将分钟转换为秒
  remainingTime.value = remainingTime.value * 60
  
  examTimer = setInterval(() => {
    remainingTime.value -= 1
    
    if (remainingTime.value === 600) {
      showTimeWarning.value = true
    }
    
    if (remainingTime.value <= 0) {
      clearInterval(examTimer)
      examTimer = null
      ElMessage.warning('考试时间已到，系统将自动提交')
      submitExam()
    }
  }, 1000)
}

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const getQuestionTypeText = (type) => {
  const map = {
    'single_choice': '单选题',
    'multiple_choice': '多选题',
    'true_false': '判断题',
    'short_answer': '简答题',
    'code': '编程题'
  }
  return map[type] || type
}


const jumpToQuestion = (index) => {
  // 保存当前多选题的答案
  if (currentQuestion.value?.question_type === 'multiple_choice') {
    userAnswers.value[currentQuestion.value.id] = selectedOptions.value.join(',')
  }
  
  currentQuestionIndex.value = index
  
  // 如果是多选题，加载已选答案
  if (currentQuestion.value.question_type === 'multiple_choice') {
    const answer = userAnswers.value[currentQuestion.value.id]
    selectedOptions.value = answer ? (answer || '').split(',') : []
  }
}

const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    jumpToQuestion(currentQuestionIndex.value - 1)
  }
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < questions.value.length - 1) {
    jumpToQuestion(currentQuestionIndex.value + 1)
  }
}

const updateMultipleChoiceAnswer = () => {
  userAnswers.value[currentQuestion.value.id] = selectedOptions.value.join(',')
}

const toggleMarkQuestion = () => {
  const qid = currentQuestion.value.id
  const index = markedQuestions.value.indexOf(qid)
  if (index > -1) {
    markedQuestions.value.splice(index, 1)
  } else {
    markedQuestions.value.push(qid)
  }
}

const jumpToMarkedQuestion = () => {
  // 跳转到第一个标记的题目
  if (markedQuestions.value.length > 0) {
    const markedId = markedQuestions.value[0]
    const index = questions.value.findIndex(q => q.id === markedId)
    if (index !== -1) {
      jumpToQuestion(index)
    }
  }
}

const submitExam = async () => {
  // 保存当前题目的答案
  if (currentQuestion.value?.question_type === 'multiple_choice') {
    userAnswers.value[currentQuestion.value.id] = selectedOptions.value.join(',')
  }
  
  submitting.value = true
  try {
    // 构造答案数组
    const answers = Object.entries(userAnswers.value).map(([question_id, answer]) => ({
      question_id: parseInt(question_id),
      answer: answer
    }))
    
    const res = await request.post(`/exams/attempts/${attemptId.value}/submit`, {
      answers
    })
    
    ElMessage.success('考试提交成功！')
    
    // 跳转到结果页
    router.push(`/exam/result/${attemptId.value}`)
  } catch (error) {
    console.error('提交考试失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
    showSubmitConfirm.value = false
  }
}
</script>

<style scoped>
.exam-page {
  min-height: 100vh;
  background-color: var(--tm-bg-elevated);
  padding-bottom: 100px;
}

.exam-header {
  background: #18181B;
  border-bottom: 1px solid var(--tm-border-color);
  padding: 16px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exam-title {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.exam-meta {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--tm-text-regular);
}

.timer {
  width: 200px;
}

.time-left {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.time-text {
  font-family: 'Consolas', monospace;
}

.exam-container {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
  margin-top: 24px;
}

.question-nav {
  background: #18181B;
  border-radius: 12px;
  padding: 20px;
  height: fit-content;
  position: sticky;
  top: 120px;
}

.nav-header {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f2f5;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.nav-item {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--tm-bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--tm-text-regular);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.nav-item:hover {
  background: #ecf5ff;
  color: #409eff;
}

.nav-item.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.nav-item.answered {
  background: #67c23a;
  color: white;
  border-color: #67c23a;
}

.nav-item.marked {
  background: #e6a23c;
  color: white;
  border-color: #e6a23c;
}

.nav-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #f0f2f5;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--tm-text-regular);
}

.legend-dot {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: var(--tm-bg-elevated);
  border: 2px solid var(--tm-border-color);
}

.legend-dot.answered {
  background: #67c23a;
  border-color: #67c23a;
}

.legend-dot.marked {
  background: #e6a23c;
  border-color: #e6a23c;
}

.question-content {
  background: #18181B;
  border-radius: 12px;
  padding: 32px;
  min-height: 500px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f2f5;
}

.question-number {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.question-body {
  margin-bottom: 32px;
}

.question-type {
  margin-bottom: 16px;
}

.question-text {
  font-size: 16px;
  line-height: 2;
  color: var(--tm-text-primary);
  margin-bottom: 24px;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.options .el-radio, .options .el-checkbox {
  font-size: 15px;
  line-height: 1.8;
}

.answer-area {
  margin-top: 16px;
}

.question-actions {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid #f0f2f5;
  padding-top: 24px;
}

.submit-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #18181B;
  border-top: 1px solid var(--tm-border-color);
  padding: 16px 0;
  z-index: 100;
  box-shadow: 0 -4px 20px 0 rgba(0, 0, 0, 0.1);
}

.submit-bar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submit-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.info-item .label {
  color: var(--tm-text-secondary);
}

.info-item .value {
  font-size: 20px;
  font-weight: bold;
}

.info-item .value.answered {
  color: #67c23a;
}

.info-item .value.unanswered {
  color: #f56c6c;
}

.info-item .value.marked {
  color: #e6a23c;
}

.info-item .total {
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.divider {
  width: 1px;
  height: 24px;
  background: var(--tm-border-color);
}

.submit-actions {
  display: flex;
  gap: 12px;
}

.submit-btn {
  font-size: 16px;
  padding: 12px 32px;
  height: auto;
}

.marked-btn {
  font-size: 14px;
  padding: 12px 20px;
  height: auto;
}

/* Markdown样式 */
.question-text {
  line-height: 2;
}

.question-text p {
  margin: 12px 0;
}

.question-text ul,
.question-text ol {
  margin: 12px 0;
  padding-left: 24px;
}

.question-text li {
  margin: 8px 0;
}

.question-text code {
  background: var(--tm-bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
}

.question-text pre {
  background: #282c34;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.question-text pre code {
  background: none;
  padding: 0;
  color: #abb2bf;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .exam-container {
    grid-template-columns: 1fr;
  }
  
  .question-nav {
    order: 2;
    position: static;
  }
  
  .question-content {
    order: 1;
    padding: 20px;
  }
  
  .exam-meta {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .timer {
    width: 100%;
  }
}
</style>
