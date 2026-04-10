<template>
  <div class="exam-result">
    <div class="container">
      <div class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回考试列表
      </div>

      <div v-if="result" class="result-container">
        <!-- 成绩概览 -->
        <div class="overview-card">
          <div class="score-section">
            <div class="score-circle" :class="result.attempt.is_passed ? 'passed' : 'failed'">
              <svg class="circle-svg" viewBox="0 0 100 100">
                <circle 
                  class="circle-bg" 
                  cx="50" 
                  cy="50" 
                  r="40" 
                  stroke-width="8" 
                  fill="none"
                />
                <circle 
                  class="circle-progress" 
                  cx="50" 
                  cy="50" 
                  r="40" 
                  stroke-width="8" 
                  fill="none"
                  :stroke-dasharray="251.2" 
                  :stroke-dashoffset="251.2 - (251.2 * result.statistics.score_rate / 100)"
                />
              </svg>
              <div class="score-content">
                <div class="score-number">{{ result.attempt.score }}</div>
                <div class="score-total">/ {{ result.exam.total_score }}</div>
                <div class="score-label">总分</div>
              </div>
            </div>
            <div class="score-info">
              <h2>{{ result.exam.title }}</h2>
              <div class="result-badge">
                <el-tag :type="result.attempt.is_passed ? 'success' : 'danger'" size="large">
                  {{ result.attempt.is_passed ? '🎉 考试通过' : '❌ 未通过' }}
                </el-tag>
              </div>
              <div class="score-meta">
                <p><strong>及格线：</strong>{{ result.exam.pass_score }}分</p>
                <p><strong>得分率：</strong>{{ result.statistics.score_rate }}%</p>
                <p><strong>考试用时：</strong>{{ result.attempt.duration }}分钟</p>
                <p><strong>完成时间：</strong>{{ result.attempt.end_time }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">{{ result.statistics.total_questions }}</div>
            <div class="stat-label">总题数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number" style="color: #67c23a;">{{ result.statistics.correct_count }}</div>
            <div class="stat-label">做对</div>
          </div>
          <div class="stat-card">
            <div class="stat-number" style="color: #f56c6c;">{{ result.statistics.wrong_count }}</div>
            <div class="stat-label">做错</div>
          </div>
          <div class="stat-card">
            <div class="stat-number" style="color: #909399;">{{ result.statistics.total_questions - result.statistics.correct_count - result.statistics.wrong_count }}</div>
            <div class="stat-label">未判分</div>
          </div>
        </div>

        <!-- 题型得分统计 -->
        <div class="section-card">
          <h3 class="section-title">题型得分情况</h3>
          <div class="type-stats">
            <div class="type-item" v-for="(stats, type) in result.statistics.question_type_stats" :key="type">
              <div class="type-header">
                <span class="type-name">{{ getQuestionTypeText(type) }}</span>
                <span class="type-score">{{ stats.score }}/{{ stats.total_score }}分</span>
              </div>
              <el-progress 
                :percentage="Math.round(stats.score / stats.total_score * 100)" 
                :color="getScoreColor(stats.score, stats.total_score)"
                :show-text="false"
              />
              <div class="type-meta">
                <span>{{ stats.correct }}/{{ stats.total }}题正确</span>
                <span>正确率 {{ Math.round(stats.correct / stats.total * 100) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 题目详情 -->
        <div class="section-card">
          <h3 class="section-title">题目详情</h3>
          <div class="question-list">
            <div 
              class="question-item" 
              v-for="(item, index) in result.result" 
              :key="index"
            >
              <div class="question-header">
                <div class="question-info">
                  <span class="question-number">第 {{ index + 1 }} 题</span>
                  <el-tag size="small" type="info">
                    {{ getQuestionTypeText(item.question.question_type) }}
                  </el-tag>
                  <span class="question-score">({{ item.question.score }}分)</span>
                </div>
                <div class="question-result">
                  <el-tag 
                    :type="item.is_correct === true ? 'success' : item.is_correct === false ? 'danger' : 'warning'"
                    size="small"
                  >
                    {{ item.is_correct === true ? '正确' : item.is_correct === false ? '错误' : '待评分' }}
                  </el-tag>
                  <span class="user-score">得分：{{ item.score || 0 }}分</span>
                </div>
              </div>
              
              <div class="question-content">
                <p v-html="renderMarkdown(item.question.content)"></p>
              </div>
              
              <!-- 选择题展示选项 -->
              <div v-if="item.question.options" class="options">
                <div 
                  class="option-item" 
                  v-for="(option, optIndex) in item.question.options" 
                  :key="optIndex"
                  :class="{
                    'correct': item.question.correct_answer.includes(String.fromCharCode(65 + optIndex)),
                    'wrong': item.user_answer.includes(String.fromCharCode(65 + optIndex)) && !item.question.correct_answer.includes(String.fromCharCode(65 + optIndex))
                  }"
                >
                  <span class="option-letter">{{ String.fromCharCode(65 + optIndex) }}.</span>
                  <span class="option-text">{{ option }}</span>
                  <el-icon v-if="item.question.correct_answer.includes(String.fromCharCode(65 + optIndex))" class="correct-icon" color="#67c23a"><Check /></el-icon>
                  <el-icon v-if="item.user_answer.includes(String.fromCharCode(65 + optIndex)) && !item.question.correct_answer.includes(String.fromCharCode(65 + optIndex))" class="wrong-icon" color="#f56c6c"><Close /></el-icon>
                </div>
              </div>
              
              <div class="answer-section">
                <div class="answer-item">
                  <div class="answer-label">你的答案：</div>
                  <div class="answer-content" :class="{ 'wrong': item.is_correct === false }">
                    {{ item.user_answer || '未作答' }}
                  </div>
                </div>
                <div class="answer-item">
                  <div class="answer-label">正确答案：</div>
                  <div class="answer-content correct">
                    {{ item.question.correct_answer }}
                  </div>
                </div>
              </div>
              
              <div class="analysis-section" v-if="item.question.analysis">
                <div class="analysis-label">答案解析：</div>
                <div class="analysis-content" v-html="renderMarkdown(item.question.analysis)"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 行动按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="reviewWrongQuestions">
            <el-icon><Edit /></el-icon>
            重做错题
          </el-button>
          <el-button type="default" @click="goToExamList">
            <el-icon><List /></el-icon>
            更多考试
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
import { ArrowLeft, Check, Close, Edit, List } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'

const router = useRouter()
const route = useRoute()
const attemptId = route.params.id

const result = ref(null)
const loading = ref(false)

onMounted(() => {
  fetchResult()
})

const fetchResult = async () => {
  loading.value = true
  try {
    const res = await request.get(`/exams/attempts/${attemptId}/result`)
    result.value = res
  } catch (error) {
    console.error('获取考试结果失败:', error)
    ElMessage.error('获取考试结果失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const goToExamList = () => {
  router.push('/exams')
}

const reviewWrongQuestions = () => {
  ElMessage.info('错题本功能开发中，敬请期待~')
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

const getScoreColor = (score, total) => {
  const rate = score / total
  if (rate >= 0.8) return '#67c23a'
  if (rate >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

const renderMarkdown = (content) => {
  return marked(content || '')
}
</script>

<style scoped>
.exam-result {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
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
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: #606266;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
}

.back-btn:hover {
  color: #409eff;
  transform: translateX(-4px);
}

.result-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overview-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.score-section {
  display: flex;
  align-items: center;
  gap: 60px;
}

.score-circle {
  position: relative;
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.circle-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  stroke: #f0f2f5;
}

.circle-progress {
  stroke: #409eff;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease;
}

.score-circle.passed .circle-progress {
  stroke: #67c23a;
}

.score-circle.failed .circle-progress {
  stroke: #f56c6c;
}

.score-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 4px;
}

.score-circle.passed .score-number {
  color: #67c23a;
}

.score-circle.failed .score-number {
  color: #f56c6c;
}

.score-total {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.score-label {
  font-size: 14px;
  color: #606266;
}

.score-info h2 {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 16px 0;
}

.result-badge {
  margin-bottom: 20px;
}

.score-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 24px;
  font-size: 14px;
  color: #606266;
  line-height: 2;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.section-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 24px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f2f5;
}

.type-stats {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.type-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.type-score {
  font-size: 14px;
  color: #606266;
}

.type-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.question-item {
  padding-bottom: 32px;
  border-bottom: 1px solid #f0f2f5;
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
  color: #303133;
}

.question-score {
  font-size: 14px;
  color: #909399;
}

.question-result {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-score {
  font-size: 14px;
  color: #606266;
}

.question-content {
  font-size: 15px;
  line-height: 2;
  color: #303133;
  margin-bottom: 16px;
}

.options {
  margin-bottom: 16px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #fafafa;
  position: relative;
}

.option-item.correct {
  background: #f0f9ff;
  border: 1px solid #67c23a;
}

.option-item.wrong {
  background: #fef0f0;
  border: 1px solid #f56c6c;
}

.option-letter {
  font-weight: bold;
  width: 20px;
  flex-shrink: 0;
}

.option-text {
  flex: 1;
}

.correct-icon, .wrong-icon {
  flex-shrink: 0;
}

.answer-section {
  margin-bottom: 16px;
}

.answer-item {
  margin-bottom: 12px;
}

.answer-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.answer-content {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
}

.answer-content.correct {
  background: #f0f9ff;
  color: #67c23a;
  border-left: 4px solid #67c23a;
}

.answer-content.wrong {
  background: #fef0f0;
  color: #f56c6c;
  border-left: 4px solid #f56c6c;
}

.analysis-section {
  padding: 16px;
  background: #ecf5ff;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.analysis-label {
  font-size: 14px;
  font-weight: 500;
  color: #409eff;
  margin-bottom: 8px;
}

.analysis-content {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 20px;
}

.loading-state {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .score-section {
    flex-direction: column;
    gap: 30px;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .overview-card, .section-card {
    padding: 20px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>
