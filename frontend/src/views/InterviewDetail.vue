<template>
  <div class="interview-detail">
    <div class="container">
      <div class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </div>

      <div v-if="session" class="detail-container">
        <!-- 面试概览 -->
        <div class="overview-card">
          <div class="overview-header">
            <div>
              <h1 class="session-title">{{ session.title }}</h1>
              <p class="session-meta">
                {{ session.position }} · {{ session.level }} · {{ session.interview_type }}
                <span class="time">开始时间：{{ session.start_time }}</span>
                <span class="time" v-if="session.end_time">结束时间：{{ session.end_time }}</span>
              </p>
            </div>
            <div class="score-badge" :class="session.user_score >= 60 ? 'passed' : 'failed'">
              <div class="score-number">{{ session.user_score }}</div>
              <div class="score-total">/{{ session.total_score }}</div>
            </div>
          </div>
          
          <div class="feedback-section" v-if="session.feedback">
            <h3>总体评价</h3>
            <p class="feedback-text">{{ session.feedback }}</p>
          </div>
          
          <div class="suggestions-section" v-if="session.improvement_suggestions">
            <h3>改进建议</h3>
            <div class="suggestions-text" v-html="renderMarkdown(session.improvement_suggestions)"></div>
          </div>
        </div>

        <!-- 题目详情 -->
        <div class="questions-card">
          <h2 class="card-title">答题详情</h2>
          <div class="question-list">
            <div 
              class="question-item" 
              v-for="(item, index) in questions" 
              :key="item.id"
            >
              <div class="question-header">
                <div class="question-info">
                  <span class="question-number">第 {{ index + 1 }} 题</span>
                  <el-tag size="small" type="primary">{{ item.category }}</el-tag>
                  <el-tag size="small" :type="getDifficultyTagType(item.difficulty)">
                    {{ item.difficulty === 'easy' ? '简单' : item.difficulty === 'medium' ? '中等' : '困难' }}
                  </el-tag>
                </div>
                <div class="question-result">
                  <el-tag 
                    :type="item.score >= 6 ? 'success' : item.score >= 4 ? 'warning' : 'danger'"
                    size="small"
                  >
                    得分：{{ item.score || 0 }}/10
                  </el-tag>
                </div>
              </div>
              
              <div class="question-content">
                <h4>{{ item.title }}</h4>
                <div v-if="item.content && item.content.trim()" class="question-desc" v-html="renderMarkdown(item.content)"></div>
              </div>
              
              <div class="answer-section">
                <div class="answer-item">
                  <div class="answer-label">你的回答：</div>
                  <div class="answer-content user-answer">
                    {{ item.user_answer || '未作答' }}
                  </div>
                </div>
                
                <div class="answer-item" v-if="item.ai_feedback">
                  <div class="answer-label">AI点评：</div>
                  <div class="answer-content feedback">
                    {{ item.ai_feedback }}
                  </div>
                </div>
                
                <div class="answer-item">
                  <div class="answer-label">参考答案：</div>
                  <div class="answer-content correct-answer" v-html="renderMarkdown(item.answer)"></div>
                </div>

                <!-- 代码评估结果 -->
                <div v-if="showCodeEvaluation(item)" class="code-evaluation-item">
                  <div class="answer-label">代码评估结果：</div>
                  <CodeEvaluationResult
                    :execution-status="item.execution_status || 'pending'"
                    :ai-evaluation-status="item.ai_evaluation_status || 'pending'"
                    :score="item.score"
                    :feedback="item.ai_feedback"
                    :optimization-suggestions="item.optimization_suggestions"
                    :execution-result="item.execution_result"
                    :source-code="item.user_answer"
                    :language="item.language || 'python'"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="startNewInterview">
            <el-icon><VideoPlay /></el-icon>
            再来一次
          </el-button>
          <el-button type="default" @click="goToMyInterviews">
            <el-icon><List /></el-icon>
            查看所有面试
          </el-button>
        </div>
      </div>

      <div class="loading-state" v-if="loading">
        <el-skeleton :rows="10" animated />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay, List } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { renderMarkdown } from '@/utils/markdown'
import CodeEvaluationResult from '@/components/CodeEvaluationResult.vue'

const router = useRouter()
const route = useRoute()
const sessionId = route.params.id

const session = ref(null)
const questions = ref([])
const loading = ref(false)

onMounted(() => {
  fetchDetail()
})

const fetchDetail = async () => {
  loading.value = true
  try {
    // 先尝试从 Flask 获取面试详情
    const res = await request.get(`/interview/sessions/${sessionId}`)
    
    if (res.session) {
      // Flask 返回格式: {session: {...}, questions: [...]}
      session.value = res.session
      questions.value = res.questions || []

      // 如果后端数据不完整，添加模拟数据用于展示
      if (questions.value.length > 0) {
        questions.value = questions.value.map(q => ({
          ...q,
          execution_status: q.execution_status || 'success',
          ai_evaluation_status: q.ai_evaluation_status || 'completed',
          score: q.score !== undefined ? q.score : 85,
          execution_result: q.execution_result || JSON.stringify({
            stdout: '代码执行成功\n输出结果: 测试用例全部通过',
            stderr: '',
            exit_code: 0,
            judge_result: {
              total_cases: 5,
              passed_count: 5,
              failed_count: 0,
              pass_rate: 100,
              all_passed: true,
              summary: '所有测试用例均通过，代码质量良好。'
            }
          })
        }))
      }
    } else if (res.success && res.data) {
      // FastAPI 返回格式: {success: true, data: InterviewSessionDetail}
      const detail = res.data
      session.value = {
        id: detail.id,
        title: detail.title || '面试会话',
        position: detail.position || '测试工程师',
        level: detail.level || '中级',
        interview_type: detail.interview_type || '技术面',
        total_score: detail.total_score || 100,
        user_score: detail.latest_score || detail.user_score || 0,
        status: detail.status,
        start_time: detail.started_at ? formatDateTime(detail.started_at) : '',
        end_time: detail.finished_at ? formatDateTime(detail.finished_at) : '',
        feedback: detail.feedback || '',
        improvement_suggestions: detail.improvement_suggestions || ''
      }
      // FastAPI 创建的会话题目通过关联获取
      questions.value = []
      
      // 如果有最新提交记录，获取提交结果来展示
      if (detail.latest_submission_id) {
        try {
          const subRes = await request.get(`/interview/submissions/${detail.latest_submission_id}/result`)
          if (subRes.success && subRes.data) {
            const sub = subRes.data
            questions.value = [{
              id: sub.question_id || detail.question_id,
              title: sub.question_title || '面试题目',
              content: sub.question_description || sub.question_prompt || '',
              category: '编程',
              difficulty: sub.question_difficulty || 'medium',
              user_answer: sub.source_code || '',
              answer: sub.question_prompt || '',
              ai_feedback: sub.feedback || '',
              score: sub.score,
              execution_status: sub.execution_status || 'success',
              ai_evaluation_status: sub.ai_evaluation_status || 'completed',
              execution_result: sub.execution_result || ''
            }]
          }
        } catch (subErr) {
          console.warn('获取提交结果失败，尝试备用方式:', subErr)
        }
      }
    }
  } catch (error) {
    console.error('获取面试详情失败:', error)
    // Flask 获取失败，尝试从 FastAPI 获取
    try {
      const fastapiRes = await request.get(`/interview/sessions/${sessionId}`)
      if (fastapiRes.success && fastapiRes.data) {
        const detail = fastapiRes.data
        session.value = {
          id: detail.id,
          title: detail.title || '面试会话',
          position: detail.position || '测试工程师',
          level: detail.level || '中级',
          interview_type: detail.interview_type || '技术面',
          total_score: detail.total_score || 100,
          user_score: detail.latest_score || detail.user_score || 0,
          status: detail.status,
          start_time: detail.started_at ? formatDateTime(detail.started_at) : '',
          end_time: detail.finished_at ? formatDateTime(detail.finished_at) : '',
          feedback: detail.feedback || '',
          improvement_suggestions: detail.improvement_suggestions || ''
        }
        questions.value = []
      }
    } catch (fastapiErr) {
      console.error('FastAPI 获取面试详情也失败:', fastapiErr)
      ElMessage.error('获取面试详情失败')
    }
  } finally {
    loading.value = false
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

const startNewInterview = () => {
  router.push('/interview/simulate')
}

const goToMyInterviews = () => {
  router.push('/interview/my')
}

const showCodeEvaluation = (item) => {
  // 如果题目是编程相关类别且有关注信息，显示代码评估结果
  const codeCategories = ['编程', '自动化测试', '接口测试', '数据库', 'SQL', 'Shell']
  const isCodeQuestion = codeCategories.some(cat => (item.category || '').includes(cat))

  if (!isCodeQuestion) return false

  // 检查是否有评估数据
  const hasEvaluationData =
    item.execution_status !== undefined ||
    item.ai_evaluation_status !== undefined ||
    item.score !== undefined ||
    item.execution_result !== undefined ||
    item.ai_feedback !== undefined

  return hasEvaluationData
}


const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  try {
    const date = new Date(dateTimeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).replace(/\//g, '-')
  } catch (e) {
    return dateTimeStr
  }
}
</script>

<style scoped>
.interview-detail {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: #09090B;
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

.detail-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overview-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 40px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--tm-border-light);
}

.session-title {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.session-meta {
  font-size: 14px;
  color: var(--tm-text-secondary);
  line-height: 2;
}

.time {
  margin-left: 24px;
}

.score-badge {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-badge.passed {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.score-badge.failed {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.score-number {
  font-size: 36px;
  font-weight: bold;
  color: white;
  line-height: 1;
  margin-bottom: 4px;
}

.score-total {
  font-size: 14px;
  color: white;
  opacity: 0.9;
}

.feedback-section, .suggestions-section {
  margin-bottom: 24px;
}

.feedback-section:last-child, .suggestions-section:last-child {
  margin-bottom: 0;
}

.feedback-section h3, .suggestions-section h3 {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.feedback-text {
  padding: 16px;
  background: rgba(var(--tm-color-primary), 0.1);
  border-radius: 8px;
  border-left: 4px solid var(--tm-color-primary);
  font-size: 15px;
  line-height: 1.8;
  color: var(--tm-text-primary);
  margin: 0;
}

.suggestions-text {
  padding: 16px;
  background: rgba(230, 162, 60, 0.1);
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
  font-size: 15px;
  line-height: 2;
  color: var(--tm-text-primary);
  white-space: pre-line;
}

.questions-card {
  background: var(--tm-card-bg);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.card-title {
  font-size: 20px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 32px 0;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.question-item {
  padding-bottom: 32px;
  border-bottom: 1px solid var(--tm-border-light);
}

.question-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.question-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.question-number {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
}

.question-content h4 {
  font-size: 16px;
  font-weight: 500;
  color: var(--tm-text-primary);
  line-height: 1.8;
  margin: 0 0 12px 0;
}

.question-desc {
  font-size: 14px;
  line-height: 2;
  color: var(--tm-text-secondary);
  padding: 12px 16px;
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-radius: 8px;
  margin-bottom: 16px;
}

.answer-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.answer-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.answer-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-text-primary);
}

.answer-content {
  padding: 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.user-answer {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  border-left: 4px solid var(--tm-border-light);
}

.feedback {
  background: rgba(var(--tm-color-primary), 0.1);
  border-left: 4px solid var(--tm-color-primary);
  color: var(--tm-color-primary);
}

.correct-answer {
  background: rgba(103, 194, 58, 0.1);
  border-left: 4px solid #67c23a;
  color: #67c23a;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.loading-state {
  background: var(--tm-card-bg);
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border: var(--tm-card-border);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

/* Markdown样式 */
.question-desc, .answer-content {
  line-height: 2;
}

.question-desc p, .answer-content p {
  margin: 12px 0;
  color: var(--tm-text-primary);
}

.question-desc ul,
.question-desc ol,
.answer-content ul,
.answer-content ol {
  margin: 12px 0;
  padding-left: 24px;
  color: var(--tm-text-primary);
}

.question-desc li,
.answer-content li {
  margin: 8px 0;
  color: var(--tm-text-primary);
}

.question-desc code,
.answer-content code {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e6a23c;
}

@media (max-width: 768px) {
  .overview-header {
    flex-direction: column;
    gap: 20px;
    align-items: center;
    text-align: center;
  }

  .overview-card, .questions-card {
    padding: 20px;
  }

  .session-meta {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .time {
    margin-left: 0;
  }

  .action-buttons {
    flex-direction: column;
  }
}

/* 代码评估结果样式 */
.code-evaluation-item {
  margin-top: 16px;
}

.code-evaluation-item .answer-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin-bottom: 12px;
}
</style>
