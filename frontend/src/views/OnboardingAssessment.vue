<template>
  <div class="assessment-page">
    <div class="assessment-container">
      <div v-if="step === 'intro'" class="step-intro">
        <div class="intro-icon">🎯</div>
        <h1 class="intro-title">入学能力测评</h1>
        <p class="intro-desc">
          完成以下 10 道测评题，我们将为你生成专属技能画像，<br/>
          并推荐最适合你的学习路径
        </p>
        <div class="intro-info">
          <div class="info-item">
            <span class="info-icon">⏱️</span>
            <span>约 5 分钟</span>
          </div>
          <div class="info-item">
            <span class="info-icon">📊</span>
            <span>5 大技能维度</span>
          </div>
          <div class="info-item">
            <span class="info-icon">🎯</span>
            <span>个性化推荐</span>
          </div>
        </div>
        <el-button
          type="primary"
          size="large"
          class="start-btn"
          @click="startAssessment"
          :loading="loading"
        >
          开始测评
        </el-button>
        <el-button
          size="large"
          class="skip-btn"
          @click="skipAssessment"
        >
          稍后再说
        </el-button>
      </div>

      <div v-else-if="step === 'quiz'" class="step-quiz">
        <div class="quiz-header">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="quiz-meta">
            <span class="meta-dimension">{{ currentQuestion.dimension_name }}</span>
            <span class="meta-count">{{ currentIndex + 1 }} / {{ questions.length }}</span>
          </div>
        </div>

        <div class="quiz-body">
          <h2 class="question-text">{{ currentQuestion.question }}</h2>
          <div class="options-list">
            <div
              v-for="(option, idx) in currentQuestion.options"
              :key="`${currentQuestion.id}-opt-${idx}`"
              class="option-item"
              :class="{
                selected: answers[currentQuestion.id] === idx,
                'option-a': idx === 0,
                'option-b': idx === 1,
                'option-c': idx === 2,
                'option-d': idx === 3,
              }"
              @click="selectOption(currentQuestion.id, idx)"
            >
              <span class="option-label">{{ optionLabels[idx] }}</span>
              <span class="option-text">{{ option }}</span>
            </div>
          </div>
        </div>

        <div class="quiz-footer">
          <el-button
            v-if="currentIndex > 0"
            @click="prevQuestion"
            size="large"
          >
            上一题
          </el-button>
          <el-button
            v-if="currentIndex < questions.length - 1"
            type="primary"
            size="large"
            @click="nextQuestion"
            :disabled="answers[currentQuestion.id] === undefined"
          >
            下一题
          </el-button>
          <el-button
            v-else
            type="primary"
            size="large"
            @click="submitAssessment"
            :disabled="answers[currentQuestion.id] === undefined"
            :loading="submitting"
          >
            提交测评
          </el-button>
        </div>
      </div>

      <div v-else-if="step === 'result'" class="step-result">
        <div class="result-header">
          <div class="result-icon">🏆</div>
          <h1 class="result-title">测评完成！</h1>
          <p class="result-subtitle">你的专属技能画像已生成</p>
        </div>

        <div class="result-score-section">
          <div class="result-score-circle">
            <svg class="circle-svg" viewBox="0 0 100 100">
              <circle class="circle-bg" cx="50" cy="50" r="40" stroke-width="8" fill="none" />
              <circle
                class="circle-progress"
                cx="50" cy="50" r="40" stroke-width="8" fill="none"
                :stroke-dasharray="251.2"
                :stroke-dashoffset="251.2 - (251.2 * animatedResultScore / 100)"
              />
            </svg>
            <div class="score-inner">
              <div class="score-value">{{ Math.round(animatedResultScore) }}</div>
              <div class="score-label">综合得分</div>
            </div>
          </div>
          <div class="result-level" :class="levelClass">{{ result.overall_level }}</div>
        </div>

        <div class="result-dimensions">
          <h3 class="section-label">技能维度分析</h3>
          <div class="dimension-list">
            <div
              v-for="dim in result.dimension_scores"
              :key="dim.key"
              class="dimension-item"
            >
              <div class="dim-header">
                <span class="dim-name">{{ dim.name }}</span>
                <span class="dim-score" :class="getScoreClass(dim.score)">{{ dim.score }}分</span>
              </div>
              <div class="dim-bar">
                <div
                  class="dim-bar-fill"
                  :style="{ width: dim.score + '%', background: getBarGradient(dim.score) }"
                ></div>
              </div>
              <span class="dim-level">{{ dim.level }}</span>
            </div>
          </div>
        </div>

        <div class="result-recommendations" v-if="result.recommended_paths?.length">
          <h3 class="section-label">为你推荐的学习路径</h3>
          <div class="rec-list">
            <div
              v-for="rec in result.recommended_paths"
              :key="rec.id"
              class="rec-item"
              @click="goToPath(rec.id)"
            >
              <div class="rec-priority">TOP {{ rec.priority }}</div>
              <div class="rec-content">
                <h4 class="rec-title">{{ rec.title }}</h4>
                <p class="rec-reason">{{ rec.reason }}</p>
              </div>
              <el-icon size="20" color="#8b5cf6"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <el-button type="primary" size="large" @click="goToHome" class="action-btn">
            进入首页
          </el-button>
          <el-button size="large" @click="goToSkillAnalysis" class="action-btn-secondary">
            查看技能详情
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const step = ref('intro')
const questions = ref([])
const answers = ref({})
const currentIndex = ref(0)
const loading = ref(false)
const submitting = ref(false)
const result = ref(null)
const animatedResultScore = ref(0)
const optionLabels = ['A', 'B', 'C', 'D']

let animFrameId = null

const currentQuestion = computed(() => questions.value[currentIndex.value] || {})
const progressPercent = computed(() => ((currentIndex.value + 1) / questions.value.length) * 100)
const levelClass = computed(() => {
  const s = result.value?.overall_score || 0
  if (s >= 80) return 'level-high'
  if (s >= 60) return 'level-mid'
  return 'level-low'
})

const animateResultScore = (target) => {
  const duration = 1500
  const startTime = performance.now()
  const step = (now) => {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedResultScore.value = target * eased
    if (progress < 1) {
      animFrameId = requestAnimationFrame(step)
    }
  }
  if (animFrameId) cancelAnimationFrame(animFrameId)
  animFrameId = requestAnimationFrame(step)
}

onMounted(async () => {
  if (userStore.assessmentCompleted) {
    router.replace('/')
    return
  }
})

onBeforeUnmount(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId)
})

const startAssessment = async () => {
  loading.value = true
  try {
    const res = await request.get('/assessment/questions')
    questions.value = res
    answers.value = {}
    currentIndex.value = 0
    step.value = 'quiz'
  } catch (error) {
    console.error('获取测评题目失败:', error)
  } finally {
    loading.value = false
  }
}

const selectOption = (questionId, index) => {
  answers.value[questionId] = index
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
  }
}

const prevQuestion = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

const submitAssessment = async () => {
  submitting.value = true
  try {
    const payload = Object.entries(answers.value).map(([qId, idx]) => ({
      question_id: Number(qId),
      selected_index: idx,
    }))
    const res = await request.post('/assessment/submit', { answers: payload })
    result.value = res
    userStore.setAssessmentCompleted({
      overall_score: res.overall_score,
      overall_level: res.overall_level,
      dimension_scores: res.dimension_scores,
    })
    step.value = 'result'
    await new Promise(r => setTimeout(r, 300))
    animateResultScore(res.overall_score)
    userStore.checkNewAchievements()
  } catch (error) {
    console.error('提交测评失败:', error)
  } finally {
    submitting.value = false
  }
}

const getScoreClass = (score) => {
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

const getBarGradient = (score) => {
  if (score >= 80) return 'linear-gradient(90deg, #8b5cf6, #d946ef)'
  if (score >= 60) return 'linear-gradient(90deg, #7c3aed, #a855f7)'
  return 'linear-gradient(90deg, #64748b, #8b5cf6)'
}

const goToPath = (id) => {
  router.push(`/learning-paths/${id}`)
}

const goToHome = () => {
  router.push('/')
}

const goToSkillAnalysis = () => {
  router.push('/skill-analysis')
}

const skipAssessment = () => {
  userStore.assessmentCompleted = true
  localStorage.setItem('assessment_completed', 'true')
  router.push('/')
}
</script>

<style scoped>
.assessment-page {
  min-height: 100vh;
  background: #0a0a14;
  background-image: radial-gradient(ellipse at 30% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
                    radial-gradient(ellipse at 70% 80%, rgba(217, 70, 239, 0.05) 0%, transparent 50%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.assessment-container {
  width: 100%;
  max-width: 720px;
}

.step-intro {
  text-align: center;
  padding: 60px 40px;
  background: rgba(18, 18, 31, 0.8);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  box-shadow: 0 4px 30px rgba(139, 92, 246, 0.1);
  backdrop-filter: blur(20px);
}

.intro-icon {
  font-size: 72px;
  margin-bottom: 24px;
}

.intro-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 16px 0;
}

.intro-desc {
  font-size: 16px;
  color: #94a3b8;
  line-height: 1.8;
  margin-bottom: 40px;
}

.intro-info {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 48px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: #c084fc;
}

.info-icon {
  font-size: 20px;
}

.start-btn {
  width: 240px;
  height: 52px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  border: none;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
}

.start-btn:hover {
  box-shadow: 0 6px 30px rgba(139, 92, 246, 0.5);
  transform: translateY(-2px);
}

.skip-btn {
  width: 240px;
  height: 52px;
  font-size: 16px;
  border-radius: 12px;
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #94a3b8;
  margin-top: 12px;
}

.skip-btn:hover {
  border-color: rgba(139, 92, 246, 0.5);
  color: #c084fc;
}

.step-quiz {
  padding: 40px;
  background: rgba(18, 18, 31, 0.8);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  box-shadow: 0 4px 30px rgba(139, 92, 246, 0.1);
  backdrop-filter: blur(20px);
}

.quiz-header {
  margin-bottom: 32px;
}

.progress-bar {
  height: 4px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  border-radius: 2px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
}

.quiz-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta-dimension {
  font-size: 14px;
  color: #c084fc;
  font-weight: 500;
  padding: 4px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.meta-count {
  font-size: 14px;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.quiz-body {
  margin-bottom: 32px;
}

.question-text {
  font-size: 20px;
  font-weight: 600;
  color: #e2e8f0;
  line-height: 1.6;
  margin: 0 0 28px 0;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: rgba(139, 92, 246, 0.04);
  border: 1px solid rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.option-item:hover {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.2);
}

.option-item.selected {
  background: rgba(139, 92, 246, 0.12);
  border-color: rgba(139, 92, 246, 0.4);
  box-shadow: 0 0 16px rgba(139, 92, 246, 0.15);
}

.option-label {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
  transition: all 0.25s ease;
}

.option-item.selected .option-label {
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  color: white;
}

.option-text {
  font-size: 15px;
  color: #cbd5e1;
  line-height: 1.5;
}

.quiz-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.step-result {
  padding: 48px 40px;
  background: rgba(18, 18, 31, 0.8);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  box-shadow: 0 4px 30px rgba(139, 92, 246, 0.1);
  backdrop-filter: blur(20px);
}

.result-header {
  text-align: center;
  margin-bottom: 36px;
}

.result-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.result-title {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
}

.result-subtitle {
  font-size: 16px;
  color: #94a3b8;
  margin: 0;
}

.result-score-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

.result-score-circle {
  position: relative;
  width: 160px;
  height: 160px;
  margin-bottom: 12px;
}

.circle-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  stroke: rgba(139, 92, 246, 0.1);
}

.circle-progress {
  stroke: #8b5cf6;
  stroke-linecap: round;
  transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 0 6px rgba(139, 92, 246, 0.6));
}

.score-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-value {
  font-size: 44px;
  font-weight: 900;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.score-label {
  font-size: 12px;
  color: #94a3b8;
  letter-spacing: 2px;
  margin-top: 4px;
}

.result-level {
  font-size: 20px;
  font-weight: 700;
  padding: 6px 20px;
  border-radius: 20px;
}

.level-high {
  color: #d946ef;
  background: rgba(217, 70, 239, 0.1);
  border: 1px solid rgba(217, 70, 239, 0.2);
}

.level-mid {
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.level-low {
  color: #64748b;
  background: rgba(100, 116, 139, 0.1);
  border: 1px solid rgba(100, 116, 139, 0.2);
}

.section-label {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0 0 20px 0;
}

.result-dimensions {
  margin-bottom: 36px;
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dimension-item {
  padding: 14px 16px;
  background: rgba(139, 92, 246, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.08);
}

.dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dim-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.dim-score {
  font-size: 16px;
  font-weight: 700;
}

.score-high {
  color: #d946ef;
}

.score-mid {
  color: #8b5cf6;
}

.score-low {
  color: #64748b;
}

.dim-bar {
  height: 4px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 6px;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
}

.dim-level {
  font-size: 12px;
  color: #94a3b8;
}

.result-recommendations {
  margin-bottom: 36px;
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rec-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.12);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.rec-item:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.25);
  transform: translateX(4px);
}

.rec-priority {
  font-size: 12px;
  font-weight: 800;
  color: #d946ef;
  background: rgba(217, 70, 239, 0.1);
  padding: 4px 10px;
  border-radius: 6px;
  flex-shrink: 0;
}

.rec-content {
  flex: 1;
}

.rec-title {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 4px 0;
}

.rec-reason {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
  line-height: 1.5;
}

.result-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.action-btn {
  width: 180px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  border: none;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
}

.action-btn-secondary {
  width: 180px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c084fc;
}
</style>
