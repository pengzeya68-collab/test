<template>
  <div class="interview-simulate-container">
    <div class="back-action-bar">
      <button class="btn-back" @click="$router.back()">&lt; 返回</button>
    </div>

    <div class="center-card-wrapper" v-if="!sessionId">
      <div class="mock-interview-card">
        <h2 class="card-title">创建模拟面试</h2>

        <div class="form-group">
          <label>应聘岗位</label>
          <input type="text" v-model="form.position" placeholder="例如：测试工程师" />
        </div>

        <div class="form-group">
          <label>岗位级别</label>
          <select v-model="form.level">
            <option value="">请选择</option>
            <option value="初级">初级</option>
            <option value="中级">中级</option>
            <option value="高级">高级</option>
            <option value="专家">专家</option>
          </select>
        </div>

        <div class="form-group">
          <label>面试类型</label>
          <select v-model="form.type">
            <option value="">请选择</option>
            <option value="技术面">技术面试</option>
            <option value="HR面">HR面试</option>
            <option value="综合面">综合面试</option>
          </select>
        </div>

        <div class="form-group row-group">
          <label>题目数量</label>
          <div class="number-input-wrap">
            <button class="num-btn" @click="form.question_count = Math.max(5, form.question_count - 1)">−</button>
            <input type="number" v-model.number="form.question_count" class="num-input" />
            <button class="num-btn" @click="form.question_count = Math.min(20, form.question_count + 1)">+</button>
          </div>
        </div>

        <div class="form-group">
          <label>考察范围</label>
          <div class="checkbox-list">
            <label
              v-for="cat in categories"
              :key="cat.value"
              class="checkbox-item"
            >
              <input type="checkbox" :value="cat.value" v-model="form.categories" />
              <span>{{ cat.label }}</span>
            </label>
            <span v-if="categories.length === 0" class="empty-hint">暂无范围可选</span>
          </div>
        </div>

        <button class="btn-start-interview" @click="createSession" :disabled="creating">
          {{ creating ? '创建中...' : '开始面试' }}
        </button>
      </div>
    </div>

    <div class="interview-session-wrapper" v-if="sessionId && session && questions.length > 0">
      <div class="interview-session-header">
        <div class="session-header-left">
          <h2 class="session-title">{{ session.title }}</h2>
          <div class="session-progress-bar">
            <span class="progress-label">第 {{ currentQuestionIndex + 1 }} 题 / 共 {{ questions.length }} 题</span>
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: Math.round((currentQuestionIndex + 1) / questions.length * 100) + '%' }"></div>
            </div>
          </div>
        </div>
        <button class="btn-end-session" @click="showCompleteConfirm = true">结束面试</button>
      </div>

      <div class="question-section" v-if="currentQuestion">
        <div class="question-meta-row">
          <span class="q-tag cat">{{ currentQuestion.category }}</span>
          <span class="q-tag" :class="'diff-' + currentQuestion.difficulty">
            {{ currentQuestion.difficulty === 'easy' ? '简单' : currentQuestion.difficulty === 'medium' ? '中等' : '困难' }}
          </span>
        </div>

        <div class="question-content">
          <h3 class="q-title">{{ currentQuestion.title }}</h3>
          <div v-if="currentQuestion.content" class="q-desc" v-html="renderMarkdown(currentQuestion.content)"></div>
        </div>

        <div class="answer-section">
          <div class="answer-top-row">
            <h4 class="answer-label">你的回答</h4>
            <button class="btn-hint" @click="showAnswerHint = !showAnswerHint">
              {{ showAnswerHint ? '收起提示' : '💡 提示一下' }}
            </button>
          </div>

          <div class="hint-box" v-if="showAnswerHint">
            请尽量详细地回答问题，体现你的思考过程。回答完成后点击提交按钮，AI 会自动为你评分和点评。
          </div>

          <div v-if="needsCodeEditor">
            <CodeEditor
              v-model="currentAnswer"
              :language="'python'"
              :template="getCodeTemplate()"
            />
            <p class="code-notice">💡 此题目为编程题，请编写代码完成要求的功能。</p>
          </div>
          <textarea
            v-else
            v-model="currentAnswer"
            class="answer-textarea"
            placeholder="请输入你的回答..."
            rows="8"
          ></textarea>

          <div class="feedback-block" v-if="currentQuestion.is_answered">
            <!-- AI 评分 -->
            <div class="feedback-score-bar">
              <span class="score-label">AI 评分</span>
              <span class="score-value" :class="getScoreClass(currentQuestion.score)">
                {{ currentQuestion.score !== null && currentQuestion.score !== undefined ? currentQuestion.score : '...' }}/100
              </span>
              <span v-if="currentQuestion.score !== null && currentQuestion.score !== undefined" class="score-level" :class="getScoreClass(currentQuestion.score)">
                {{ getScoreLevel(currentQuestion.score) }}
              </span>
              <span v-if="currentQuestion.score === null || currentQuestion.score === undefined" class="score-evaluating">评估中...</span>
            </div>

            <!-- 结构化反馈 -->
            <div v-if="currentQuestion.parsed_feedback" class="feedback-sections">
              <div class="fb-section fb-overview" v-if="currentQuestion.parsed_feedback.feedback">
                <div class="fb-title">总评</div>
                <div class="fb-text">{{ currentQuestion.parsed_feedback.feedback }}</div>
              </div>
              <div class="fb-section fb-strengths" v-if="currentQuestion.parsed_feedback.strengths?.length">
                <div class="fb-title">优点</div>
                <ul><li v-for="(s, i) in currentQuestion.parsed_feedback.strengths" :key="i">{{ s }}</li></ul>
              </div>
              <div class="fb-section fb-weaknesses" v-if="currentQuestion.parsed_feedback.weaknesses?.length">
                <div class="fb-title">不足</div>
                <ul><li v-for="(w, i) in currentQuestion.parsed_feedback.weaknesses" :key="i">{{ w }}</li></ul>
              </div>
              <div class="fb-section fb-suggestion" v-if="currentQuestion.parsed_feedback.suggestion">
                <div class="fb-title">改进建议</div>
                <div class="fb-text">{{ currentQuestion.parsed_feedback.suggestion }}</div>
              </div>
            </div>
            <!-- 降级：无结构化数据时显示纯文本 -->
            <div v-else-if="currentQuestion.ai_feedback" class="feedback-text">{{ currentQuestion.ai_feedback }}</div>

            <div class="follow-up-block" v-if="currentQuestion.follow_up_question">
              <div class="feedback-divider">🔍 面试官追问</div>
              <div class="follow-up-q">
                <p>{{ currentQuestion.follow_up_question }}</p>
                <p class="follow-up-hint">{{ currentQuestion.follow_up_hint }}</p>
              </div>
              <textarea
                v-model="currentQuestion.follow_up_answer"
                class="answer-textarea"
                rows="3"
                placeholder="请输入你的追问回答..."
              ></textarea>
              <button class="btn-submit-follow" @click="submitFollowUp" :disabled="followUpSubmitting">
                {{ followUpSubmitting ? '提交中...' : '提交追问回答' }}
              </button>
              <div v-if="currentQuestion.follow_up_feedback" class="follow-up-result">
                {{ currentQuestion.follow_up_feedback }}
              </div>
            </div>

            <div class="follow-up-trigger" v-if="!currentQuestion.follow_up_question && !currentQuestion.follow_up_skipped">
              <button class="btn-follow-up" @click="requestFollowUp" :disabled="followUpLoading">
                {{ followUpLoading ? '获取中...' : '🔍 面试官追问' }}
              </button>
              <span v-if="getCostText('interview_follow_up')" class="ai-cost-hint">{{ getCostText('interview_follow_up') }}</span>
              <button class="btn-skip" @click="currentQuestion.follow_up_skipped = true">跳过追问</button>
            </div>

            <!-- 参考答案（默认展开） -->
            <details class="ref-answer" open>
              <summary>参考答案</summary>
              <div v-html="renderMarkdown(currentQuestion.answer)"></div>
            </details>
          </div>
        </div>

        <div class="question-nav-buttons">
          <button :disabled="currentQuestionIndex === 0" @click="prevQuestion">上一题</button>
          <span v-if="getCostText('interview_text_eval') && !currentQuestion.is_answered" class="ai-cost-hint">提交答案消耗 {{ getCostText('interview_text_eval') }}</span>
          <button
            v-if="!currentQuestion.is_answered"
            class="btn-submit"
            @click="submitAnswer"
            :disabled="submitting"
          >
            {{ submitting ? '提交中...' : '提交回答' }}
          </button>
          <button
            v-else
            class="btn-submit"
            :disabled="currentQuestionIndex === questions.length - 1"
            @click="nextQuestion"
          >
            下一题
          </button>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showResultDialog"
      title="面试报告"
      width="680px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div v-if="result" class="report-content">
        <!-- 总分徽章 -->
        <div class="report-hero">
          <div class="score-badge" :class="result.score >= 60 ? 'passed' : 'failed'">
            <div class="big-score">{{ result.score }}</div>
            <div class="score-unit">分</div>
          </div>
          <div class="score-meta">
            <div class="level-badge" :class="getScoreClass(result.score)">{{ result.report?.overall_level || '未评级' }}</div>
            <div class="score-summary">{{ result.report?.summary || `本次面试共 ${result.total_questions} 题，已答 ${result.answered_questions} 题` }}</div>
          </div>
        </div>

        <!-- 强项 -->
        <div class="report-section" v-if="result.report?.strengths?.length">
          <h4>强项</h4>
          <ul><li v-for="(s, i) in result.report.strengths" :key="i">{{ s }}</li></ul>
        </div>

        <!-- 弱项 -->
        <div class="report-section" v-if="result.report?.weaknesses?.length">
          <h4>待提升</h4>
          <ul><li v-for="(w, i) in result.report.weaknesses" :key="i">{{ w }}</li></ul>
        </div>

        <!-- 分数范围 -->
        <div class="report-section" v-if="result.report?.score_range">
          <h4>分数统计</h4>
          <div class="score-stats">
            <span>最高分: <strong>{{ result.report.score_range.max }}</strong></span>
            <span>最低分: <strong>{{ result.report.score_range.min }}</strong></span>
            <span>通过率: <strong>{{ result.report.pass_rate }}%</strong></span>
          </div>
        </div>

        <!-- 改进计划 -->
        <div class="report-section" v-if="result.report?.improvement_plan?.length">
          <h4>改进计划</h4>
          <ol><li v-for="(p, i) in result.report.improvement_plan" :key="i">{{ p }}</li></ol>
        </div>
      </div>
      <template #footer>
        <el-button @click="goToDetail">查看详情</el-button>
        <el-button type="primary" @click="restart">再来一次</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showCompleteConfirm"
      title="确认结束面试"
      width="400px"
    >
      <p>你确定要结束本次面试吗？结束后将无法继续答题。</p>
      <template #footer>
        <el-button @click="showCompleteConfirm = false">取消</el-button>
        <el-button type="danger" @click="completeInterview" :disabled="completing">确认结束</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay, Star } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useAICosts } from '@/composables/useAICosts'
import { renderMarkdown } from '@/utils/markdown'
import CodeEditor from '@/components/CodeEditor.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { fetchCosts, getCostText } = useAICosts()

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
const followUpLoading = ref(false)
const followUpSubmitting = ref(false)

const currentQuestion = computed(() => {
  return questions.value[currentQuestionIndex.value]
})

const needsCodeEditor = computed(() => {
  if (!currentQuestion.value) return false
  // 优先使用 language 字段判断：text 表示文本题，其余视为代码题
  const lang = (currentQuestion.value.language || '').toLowerCase()
  if (lang === 'text' || lang === '中文' || lang === '通用') return false
  if (['python', 'java', 'sql', 'shell', 'javascript', 'go', 'c', 'c++'].some(l => lang.includes(l))) return true
  // 降级：用 category 判断（仅当 language 不明确时）
  const category = currentQuestion.value.category || ''
  const codeCategories = ['编程', '自动化测试', '接口测试', '数据库', 'SQL', 'Shell']
  return codeCategories.some(cat => category.includes(cat))
})

onMounted(() => {
  fetchCosts()
  fetchCategories()
  const idFromUrl = route.query.session_id
  if (idFromUrl) {
    sessionId.value = Number(idFromUrl)
    fetchSession()
  }
})

const fetchCategories = async () => {
  try {
    const res = await request.get('/interview/questions', { params: { page: 1, size: 100 } })
    const fetchedQuestions = res.items || res.data?.items || []
    const categorySet = new Set(fetchedQuestions.map(q => q.category || '其他').filter(Boolean))
    categories.value = Array.from(categorySet).map(c => ({ label: c, value: c }))
    form.categories = categories.value.filter(c => c.value !== 'HR面' && c.value !== '职业规划').map(c => c.value)
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
    const res = await request.post('/interview/sessions/batch', form)
    const data = res.data || res
    sessionId.value = data.session_id
    session.value = data.session
    questions.value = data.questions || []

    if (questions.value.length > 0) {
      currentAnswer.value = questions.value[0].user_answer || ''
    }

    ElMessage.success(`面试会话创建成功！共${data.total_questions || questions.value.length}道题目`)
  } catch (error) {
    console.error('创建面试会话失败:', error)
    ElMessage.error('创建失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const fetchSession = async () => {
  creating.value = true
  try {
    const res = await request.get(`/interview/sessions/${sessionId.value}`)
    const data = res.data || res
    session.value = data.session
    questions.value = data.questions || []

    if (questions.value.length > 0) {
      const firstUnanswered = questions.value.findIndex(q => !q.is_answered)
      currentQuestionIndex.value = firstUnanswered >= 0 ? firstUnanswered : 0
      currentAnswer.value = questions.value[currentQuestionIndex.value].user_answer || ''
    }
  } catch (error) {
    console.error('获取面试会话失败:', error)
    ElMessage.error('获取面试信息失败')
  } finally {
    creating.value = false
  }
}

const getDifficultyTagType = (difficulty) => {
  const map = { 'easy': 'success', 'medium': 'warning', 'hard': 'danger' }
  return map[difficulty] || 'info'
}

const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    if (currentQuestion.value) {
      currentQuestion.value.user_answer = currentAnswer.value
    }
    currentQuestionIndex.value -= 1
    currentAnswer.value = questions.value[currentQuestionIndex.value].user_answer || ''
  }
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < questions.value.length - 1) {
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
    const isCode = needsCodeEditor.value
    const res = await request.post(`/interview/sessions/${sessionId.value}/submissions`, {
      session_id: sessionId.value,
      language: isCode ? 'python' : 'text',
      source_code: currentAnswer.value.trim(),
    }, { timeout: 120000 })

    const subData = res.data || res
    currentQuestion.value.is_answered = true
    currentQuestion.value.record_id = subData.id
    currentQuestion.value.user_answer = currentAnswer.value.trim()

    const checkResult = async (attempts = 0) => {
      if (attempts > 20) {
        currentQuestion.value.ai_feedback = 'AI评估超时，请稍后刷新查看'
        return
      }
      try {
        const subRes = await request.get(`/interview/submissions/${subData.id}`)
        const sub = subRes.data || subRes
        if (sub.score !== null && sub.score !== undefined) {
          currentQuestion.value.score = sub.score
          currentQuestion.value.ai_feedback = sub.feedback || '评估完成'
          currentQuestion.value.parsed_feedback = sub.parsed_feedback || null
          return
        }
      } catch {}
      await new Promise(r => setTimeout(r, 2000))
      await checkResult(attempts + 1)
    }

    setTimeout(() => checkResult(), 2000)
    ElMessage.success('回答提交成功，AI正在评估...')
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
    const data = res.data || res
    const report = data.report || {}
    result.value = {
      score: data.score || 0,
      total_questions: data.total_questions || 0,
      answered_questions: data.answered_questions || 0,
      report: report,
    }
    showResultDialog.value = true
    showCompleteConfirm.value = false
    userStore.checkNewAchievements()
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
  sessionId.value = null
  session.value = null
  questions.value = []
  currentQuestionIndex.value = 0
  currentAnswer.value = ''
  showAnswerHint.value = false
  showResultDialog.value = false
  result.value = null
}

const getCodeTemplate = () => {
  if (!currentQuestion.value) return ''
  const content = currentQuestion.value.content || ''
  if (content.includes('def ') || content.includes('function')) {
    return content
  }
  return '# 请在此处编写你的代码\n# 完成题目要求的功能'
}

const getScoreClass = (score) => {
  if (score === null || score === undefined) return ''
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

const getScoreLevel = (score) => {
  if (score === null || score === undefined) return ''
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '中等'
  if (score >= 60) return '及格'
  return '不及格'
}

const requestFollowUp = async () => {
  if (!currentQuestion.value) return
  followUpLoading.value = true
  try {
    const res = await request.post('/interview/follow-up', {
      question_title: currentQuestion.value.title,
      user_answer: currentAnswer.value,
      ai_feedback: currentQuestion.value.ai_feedback || '',
      score: currentQuestion.value.score || 0,
    }, { timeout: 120000 })
    currentQuestion.value.follow_up_question = res.follow_up_question
    currentQuestion.value.follow_up_hint = res.hint
    currentQuestion.value.follow_up_type = res.follow_up_type
  } catch (error) {
    console.error('获取追问失败:', error)
    ElMessage.error('获取追问失败')
  } finally {
    followUpLoading.value = false
  }
}

const submitFollowUp = async () => {
  if (!currentQuestion.value?.follow_up_answer?.trim()) {
    ElMessage.warning('请输入追问回答')
    return
  }
  followUpSubmitting.value = true
  try {
    const res = await request.post('/interview/evaluate', {
      question_id: currentQuestion.value.id,
      language: 'text',
      source_code: currentQuestion.value.follow_up_answer,
    })
    currentQuestion.value.follow_up_feedback = res.data?.feedback || '回答已收到，继续保持！'
    ElMessage.success('追问回答已提交')
  } catch (error) {
    currentQuestion.value.follow_up_feedback = '回答已收到，面试官对你的追问回答表示认可。'
    ElMessage.success('追问回答已提交')
  } finally {
    followUpSubmitting.value = false
  }
}
</script>

<style scoped>
.interview-simulate-container {
  width: 100%;
  min-height: calc(100vh - 80px);
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
}

.back-action-bar {
  position: absolute;
  top: 40px;
  left: 40px;
}

.btn-back {
  background: transparent;
  color: var(--tm-text-regular);
  border: 1px solid var(--tm-border-light);
  padding: 8px 18px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}
.btn-back:hover {
  color: var(--tm-text-primary);
  border-color: var(--tm-color-primary);
}

.center-card-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.mock-interview-card {
  width: 480px;
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  box-shadow: 0 0 20px rgba(var(--tm-color-primary-rgb), 0.05);
}

.card-title {
  text-align: center;
  color: var(--tm-text-primary);
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
}

.form-group {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.form-group label {
  width: 80px;
  color: var(--tm-text-regular);
  font-size: 14px;
  text-align: right;
  padding-top: 8px;
  flex-shrink: 0;
}
.form-group input,
.form-group select {
  flex: 1;
  background: var(--tm-bg-page);
  border: 1px solid #27272a;
  color: var(--tm-text-primary);
  padding: 10px 12px;
  border-radius: 6px;
  outline: none;
  font-size: 14px;
}
.form-group input:focus,
.form-group select:focus {
  border-color: rgba(var(--tm-color-primary-rgb), 0.4);
}

.row-group .number-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.num-btn {
  background: var(--bg-surface-hover);
  border: none;
  color: var(--tm-text-regular);
  width: 32px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.num-btn:hover { background: var(--bg-surface-hover); }
.num-input {
  width: 60px !important;
  text-align: center;
  flex: none !important;
}

.checkbox-list {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding-top: 2px;
}
.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--tm-text-regular);
  font-size: 13px;
  cursor: pointer;
}
.checkbox-item input[type="checkbox"] {
  accent-color: var(--tm-color-primary);
  width: 16px;
  height: 16px;
  flex: none;
}
.empty-hint {
  color: #52525b;
  font-size: 13px;
}

.btn-start-interview {
  margin-top: 8px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.3);
  transition: all 0.3s ease;
}
.btn-start-interview:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(var(--tm-color-primary-rgb), 0.45);
}
.btn-start-interview:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* ========== Interview Session ========== */
.interview-session-wrapper {
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.interview-session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 24px 28px;
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 12px;
}

.session-header-left {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 14px;
}

.session-progress-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}
.progress-label {
  font-size: 13px;
  color: var(--tm-text-regular);
  white-space: nowrap;
}
.progress-track {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px;
  transition: width 0.4s ease;
}

.btn-end-session {
  background: rgba(248, 113, 113, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.25);
  color: #f87171;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn-end-session:hover {
  background: rgba(248, 113, 113, 0.25);
}

/* ========== Question Section ========== */
.question-section {
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.question-meta-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.q-tag {
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: var(--bg-surface-hover);
  color: var(--tm-text-regular);
}
.q-tag.cat { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }
.q-tag.diff-easy, .q-tag.diff-beginner { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.q-tag.diff-medium, .q-tag.diff-intermediate { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
.q-tag.diff-hard, .q-tag.diff-advanced { background: rgba(248, 113, 113, 0.12); color: #f87171; }

.q-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text-primary);
  line-height: 1.8;
  margin: 0 0 12px;
}

.q-desc {
  font-size: 15px;
  line-height: 1.8;
  color: var(--tm-text-regular);
  padding: 16px;
  background: var(--tm-card-bg);
  border-radius: 8px;
  border-left: 3px solid #27272a;
}

/* ========== Answer ========== */
.answer-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.answer-label {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0;
}
.btn-hint {
  background: none;
  border: none;
  color: #fbbf24;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
}
.hint-box {
  padding: 14px 16px;
  background: rgba(251, 191, 36, 0.06);
  border-radius: 8px;
  border: 1px solid rgba(251, 191, 36, 0.15);
  font-size: 13px;
  color: #fcd34d;
  margin-bottom: 14px;
  line-height: 1.6;
}

.answer-textarea {
  width: 100%;
  box-sizing: border-box;
  background: var(--tm-bg-page);
  border: 1px solid #27272a;
  border-radius: 8px;
  color: var(--tm-text-regular);
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.8;
  resize: vertical;
  outline: none;
  font-family: inherit;
}
.answer-textarea:focus {
  border-color: rgba(var(--tm-color-primary-rgb), 0.4);
}
.code-notice {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin-top: 8px;
}

/* ========== Feedback ========== */
.feedback-block {
  margin-top: 24px;
}
.feedback-divider {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  padding-bottom: 10px;
  border-bottom: 1px solid #27272a;
  margin-bottom: 14px;
}
.score-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: var(--tm-text-regular);
  margin-bottom: 14px;
}
.star-score {
  font-size: 22px;
  font-weight: 900;
  color: var(--tm-color-primary);
}
.feedback-text {
  padding: 16px;
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  border-radius: 8px;
  border-left: 3px solid var(--tm-color-primary);
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
  margin-bottom: 16px;
}

/* ========== Follow Up ========== */
.follow-up-block {
  margin-top: 16px;
}
.follow-up-q {
  padding: 14px 16px;
  background: rgba(251, 191, 36, 0.06);
  border-radius: 8px;
  border: 1px solid rgba(251, 191, 36, 0.15);
  margin-bottom: 14px;
}
.follow-up-q p {
  margin: 0;
  color: #fcd34d;
  font-size: 14px;
  line-height: 1.6;
}
.follow-up-hint {
  font-size: 12px !important;
  color: var(--tm-text-regular) !important;
  margin-top: 6px !important;
}
.btn-submit-follow {
  margin-top: 8px;
  padding: 8px 22px;
  background: linear-gradient(135deg, #fbbf24, #d97706);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-submit-follow:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(251,191,36,0.3); }
.btn-submit-follow:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.follow-up-result {
  margin-top: 12px;
  padding: 12px 16px;
  background: rgba(52, 211, 153, 0.06);
  border-radius: 8px;
  font-size: 14px;
  color: #34d399;
  line-height: 1.6;
}

.follow-up-trigger {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
.btn-follow-up {
  padding: 8px 18px;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-follow-up:hover { background: rgba(251, 191, 36, 0.2); }
.btn-follow-up:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-skip {
  padding: 8px 18px;
  background: transparent;
  border: 1px solid var(--tm-border-light);
  color: var(--tm-text-regular);
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-skip:hover { border-color: var(--tm-color-primary); color: var(--tm-color-primary); }

/* ========== Reference Answer ========== */
.ref-answer {
  margin-top: 16px;
}
.ref-answer summary {
  font-size: 14px;
  color: var(--tm-text-regular);
  cursor: pointer;
  font-weight: 500;
  padding: 8px 0;
}
.ref-answer summary:hover { color: var(--tm-color-primary); }
.ref-answer > div {
  padding: 16px;
  background: var(--tm-card-bg);
  border-radius: 8px;
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
}

/* ========== Nav Buttons ========== */
.question-nav-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24px;
  border-top: 1px solid #27272a;
}
.question-nav-buttons button {
  padding: 10px 28px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--tm-border-light);
  color: var(--tm-text-regular);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.question-nav-buttons button:hover:not(:disabled) {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
}
.question-nav-buttons button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-submit {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark)) !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 2px 12px rgba(var(--tm-color-primary-rgb), 0.3);
}
.btn-submit:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(var(--tm-color-primary-rgb), 0.45) !important;
  transform: translateY(-1px);
}

/* ========== Result Modal ========== */
.result-content {
  padding: 10px 0;
}
.result-score-row {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid #27272a;
}
.score-badge {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.score-badge.passed {
  background: linear-gradient(135deg, #34d399, #059669);
}
.score-badge.failed {
  background: linear-gradient(135deg, #f87171, #dc2626);
}
.big-score {
  font-size: 34px;
  font-weight: 900;
  color: #fff;
  line-height: 1;
}
.score-unit {
  font-size: 13px;
  color: rgba(255,255,255,0.8);
}
.result-info h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 10px;
}
.result-info p {
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.8;
  margin: 0;
}
.suggestions-box {
  padding: 20px;
  background: rgba(251, 191, 36, 0.06);
  border-radius: 8px;
  border-left: 3px solid #fbbf24;
}
.suggestions-box h4 {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 14px;
}
.suggestions-box div {
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
  white-space: pre-line;
}

/* ========== Markdown in dialogs ========== */
.question-section :deep(p),
.suggestions-box :deep(p),
.ref-answer :deep(p) {
  margin: 10px 0;
}
.question-section :deep(code),
.suggestions-box :deep(code),
.ref-answer :deep(code) {
  background: var(--tm-card-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #fbbf24;
}
.question-section :deep(ul),
.question-section :deep(ol),
.suggestions-box :deep(ul),
.suggestions-box :deep(ol) {
  padding-left: 24px;
}

@media (max-width: 768px) {
  .interview-simulate-container { padding: 24px; }
  .back-action-bar { top: 24px; left: 24px; }
  .mock-interview-card { padding: 24px; }
  .interview-session-header { flex-direction: column; }
  .question-section { padding: 20px; }
  .result-score-row { flex-direction: column; text-align: center; }
}

.ai-cost-hint {
  font-size: 11px;
  color: #ffa502;
  margin-left: 8px;
  white-space: nowrap;
}

/* ========== Score Bar ========== */
.feedback-score-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #27272a;
  margin-bottom: 16px;
}
.score-label {
  font-size: 14px;
  color: var(--tm-text-regular);
}
.score-value {
  font-size: 28px;
  font-weight: 900;
}
.score-value.score-high { color: #34d399; }
.score-value.score-mid { color: #fbbf24; }
.score-value.score-low { color: #f87171; }
.score-level {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 4px;
}
.score-level.score-high { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.score-level.score-mid { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
.score-level.score-low { background: rgba(248, 113, 113, 0.12); color: #f87171; }
.score-evaluating {
  font-size: 13px;
  color: var(--tm-text-secondary);
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ========== Feedback Sections ========== */
.feedback-sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}
.fb-section {
  padding: 14px 16px;
  border-radius: 8px;
  border-left: 3px solid;
}
.fb-overview {
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  border-left-color: var(--tm-color-primary);
}
.fb-strengths {
  background: rgba(52, 211, 153, 0.06);
  border-left-color: #34d399;
}
.fb-weaknesses {
  background: rgba(251, 191, 36, 0.06);
  border-left-color: #fbbf24;
}
.fb-suggestion {
  background: rgba(99, 102, 241, 0.06);
  border-left-color: #6366f1;
}
.fb-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin-bottom: 8px;
}
.fb-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
}
.fb-section ul {
  margin: 0;
  padding-left: 20px;
}
.fb-section li {
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
  margin-bottom: 4px;
}

/* ========== Report Dialog ========== */
.report-content {
  padding: 10px 0;
}
.report-hero {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid #27272a;
}
.score-meta {
  flex: 1;
}
.level-badge {
  display: inline-block;
  font-size: 18px;
  font-weight: 700;
  padding: 4px 16px;
  border-radius: 6px;
  margin-bottom: 10px;
}
.level-badge.score-high { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.level-badge.score-mid { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.level-badge.score-low { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.score-summary {
  font-size: 15px;
  color: var(--tm-text-regular);
  line-height: 1.6;
}
.report-section {
  margin-bottom: 20px;
}
.report-section h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #27272a;
}
.report-section ul, .report-section ol {
  margin: 0;
  padding-left: 24px;
}
.report-section li {
  font-size: 14px;
  line-height: 1.8;
  color: var(--tm-text-regular);
  margin-bottom: 4px;
}
.score-stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--tm-text-regular);
}
.score-stats strong {
  color: var(--tm-text-primary);
}
</style>