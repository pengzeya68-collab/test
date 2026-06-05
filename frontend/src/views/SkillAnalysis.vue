<template>
  <div class="skill-analysis-container">
    <header class="analysis-header">
      <div class="header-titles">
        <h1 class="page-title">技能分析看板</h1>
        <p class="page-subtitle">基于你的练习与面试表现，全方位剖析核心技术栈的掌握情况</p>
      </div>
      <div class="overall-badge">
        <span class="badge-label">综合胜任率</span>
        <span class="badge-value">{{ Math.round(animatedScore) }}<span class="badge-unit">分</span></span>
        <span class="badge-level">{{ overallLevel }}</span>
      </div>
    </header>

    <main class="analysis-main-content">
      <section class="dashboard-section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="title-dot">◈</span>
            能力评估与提升建议
          </h2>
          <div class="title-glow-line"></div>
        </div>
        <div class="overview-card">
          <div class="score-section">
            <div class="score-circle">
              <svg class="circle-svg" viewBox="0 0 100 100">
                <circle
                  class="circle-bg"
                  cx="50" cy="50" r="40"
                  stroke-width="8" fill="none"
                />
                <circle
                  class="circle-progress"
                  cx="50" cy="50" r="40"
                  stroke-width="8" fill="none"
                  :stroke-dasharray="251.2"
                  :stroke-dashoffset="251.2 - (251.2 * animatedScore / 100)"
                />
              </svg>
              <div class="score-inner">
                <span class="score-num">{{ Math.round(animatedScore) }}</span>
                <span class="score-unit">分</span>
              </div>
            </div>
            <div class="score-info">
              <h3>能力评估</h3>
              <p class="level-desc">{{ levelDescription }}</p>
              <div class="improvement-tip">
                <span class="tip-icon">💡</span>
                <span>{{ improvementTip }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="charts-grid">
        <div class="chart-card">
          <div class="section-header">
            <h2 class="section-title">
              <span class="title-dot">◈</span>
              技能雷达图
            </h2>
            <div class="title-glow-line"></div>
          </div>
          <div class="chart-body" ref="radarChartRef">
            <v-chart :option="radarOption" :autoresize="true" style="width: 100%; height: 350px;" />
          </div>
        </div>

        <div class="chart-card">
          <div class="section-header">
            <h2 class="section-title">
              <span class="title-dot">◈</span>
              技术栈掌握度
            </h2>
            <div class="title-glow-line"></div>
          </div>
          <div class="chart-body" ref="barChartRef">
            <v-chart :option="barOption" :autoresize="true" style="width: 100%; height: 350px;" />
          </div>
        </div>

        <div class="chart-card chart-card-full">
          <div class="section-header">
            <h2 class="section-title">
              <span class="title-dot">◈</span>
              技能提升进度
            </h2>
            <div class="title-glow-line"></div>
          </div>
          <div class="chart-body" ref="lineChartRef">
            <v-chart :option="lineOption" :autoresize="true" style="width: 100%; height: 350px;" />
          </div>
        </div>
      </div>

      <section class="dashboard-section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="title-dot">◈</span>
            核心技术栈掌握详情
          </h2>
          <div class="title-glow-line"></div>
        </div>
        <div class="skill-cards-list">
          <div
            class="skill-block-card"
            v-for="(skill, idx) in skills"
            :key="skill.key"
            @click="viewSkillDetail(skill)"
          >
            <div class="card-top-bar">
              <div class="module-title-wrapper">
                <span class="module-index">{{ String(idx + 1).padStart(2, '0') }}</span>
                <h3 class="module-name">{{ skill.name }}</h3>
              </div>
              <div class="status-group">
                <span class="score-badge" :class="getScoreClass(skill.score)">{{ skill.score }}分</span>
                <span class="status-tag" :class="getLevelClass(skill.level)">{{ skill.level }}</span>
              </div>
            </div>

            <div class="card-analysis-body">
              <p class="analysis-text">{{ skill.description }}</p>
            </div>

            <div class="skill-progress-row">
              <div class="skill-progress-bar">
                <div
                  class="skill-progress-fill"
                  :style="{ width: skill.score + '%', background: getScoreGradient(skill.score) }"
                ></div>
              </div>
            </div>

            <div class="card-footer-tags">
              <div class="suggestion-row">
                <span class="suggestion-icon">💡</span>
                <span class="suggestion-text">{{ skill.suggestion }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <div class="modal-overlay" v-if="detailVisible" @click.self="detailVisible = false">
      <div class="modal-card">
        <div class="modal-header">
          <h2 class="modal-title">技能详情</h2>
          <button class="modal-close" @click="detailVisible = false">✕</button>
        </div>
        <div class="modal-body" v-if="selectedSkill">
          <div class="detail-header">
            <div class="detail-score">
              <span class="detail-score-num">{{ selectedSkill.score }}</span>
              <span class="detail-score-unit">分</span>
            </div>
            <div class="detail-info">
              <h3>{{ selectedSkill.name }}</h3>
              <p>{{ selectedSkill.description }}</p>
              <span class="detail-level-tag" :class="getLevelClass(selectedSkill.level)">{{ selectedSkill.level }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>提升建议</h4>
            <p class="detail-suggestion">{{ selectedSkill.suggestion }}</p>
          </div>

          <div class="detail-section" v-if="selectedSkill.recommended_exercises?.length > 0">
            <h4>推荐练习</h4>
            <div class="exercise-list">
              <div
                class="exercise-item"
                v-for="ex in selectedSkill.recommended_exercises"
                :key="ex.id"
                @click="goToExercise(ex.id)"
              >
                <div class="exercise-info">
                  <span class="exercise-title">{{ ex.title }}</span>
                  <span class="exercise-diff-tag" :class="'diff-' + ex.difficulty">{{ getDifficultyText(ex.difficulty) }}</span>
                </div>
                <span class="exercise-time">{{ ex.time_estimate }}分钟</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent,
  GridComponent
} from 'echarts/components'
import request from '@/utils/request'

use([
  CanvasRenderer,
  RadarChart,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent,
  GridComponent
])

const router = useRouter()

const PRIMARY_PURPLE = 'var(--tm-color-primary)'
const PRIMARY_MAGENTA = '#d946ef'
const LIGHT_PURPLE = '#c084fc'
const TEXT_LIGHT = '#e2e8f0'
const TEXT_DIM = '#94a3b8'

const DEFAULT_SKILLS = [
  { key: 'api_automation', name: '接口自动化测试', score: 82, level: '熟练', description: '掌握 REST/GraphQL 接口测试，熟练使用 Pytest + Requests 构建自动化框架', suggestion: '建议深入学习契约测试(Pact)与接口Mock服务治理' },
  { key: 'python_backend', name: 'Python 后端开发', score: 75, level: '掌握', description: '熟练使用 FastAPI/Flask 开发测试工具与数据服务', suggestion: '建议学习异步编程(asyncio)与微服务架构设计' },
  { key: 'vue_frontend', name: 'Vue 前端开发', score: 68, level: '掌握', description: '掌握 Vue3 + Element Plus 构建测试管理平台', suggestion: '建议学习 Pinia 状态管理与组件库深度定制' },
  { key: 'cicd_pipeline', name: 'CI/CD 流水线部署', score: 70, level: '掌握', description: '掌握 Jenkins/GitLab CI 构建自动化测试流水线', suggestion: '建议学习 GitHub Actions 与 ArgoCD 持续交付' },
  { key: 'cloud_native', name: '云原生与自动化工具', score: 65, level: '了解', description: '掌握 Docker/K8s 容器化部署与自动化运维工具', suggestion: '建议学习 Helm Chart 与 Istio 服务网格' }
]

const DEFAULT_RADAR_DATA = {
  indicators: [
    { name: '接口自动化测试', max: 100 },
    { name: 'Python 后端开发', max: 100 },
    { name: 'Vue 前端开发', max: 100 },
    { name: 'CI/CD 流水线部署', max: 100 },
    { name: '云原生与自动化工具', max: 100 }
  ],
  user_data: [82, 75, 68, 70, 65],
  industry_data: [70, 65, 60, 55, 50]
}

const DEFAULT_LINE_DATA = {
  months: ['10月', '11月', '12月', '1月', '2月', '3月'],
  scores: [58, 63, 68, 72, 76, 82]
}

const skills = ref(DEFAULT_SKILLS)
const radarData = ref(DEFAULT_RADAR_DATA)
const lineData = ref(DEFAULT_LINE_DATA)
const overallScore = ref(82)
const overallLevel = ref('熟练')
const animatedScore = ref(0)
const detailVisible = ref(false)
const selectedSkill = ref(null)
const loading = ref(false)

const radarChartRef = ref(null)
const barChartRef = ref(null)
const lineChartRef = ref(null)

let animationFrameId = null

const animateScore = (target) => {
  const duration = 1500
  const startTime = performance.now()
  const step = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedScore.value = 0 + (target - 0) * eased
    if (progress < 1) {
      animationFrameId = requestAnimationFrame(step)
    }
  }
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  animationFrameId = requestAnimationFrame(step)
}

const levelDescription = computed(() => {
  const map = {
    '入门': '你刚刚进入测试开发领域，还有很大的提升空间，加油！',
    '了解': '你已经掌握了基础的测试开发知识，可以尝试更多实战练习。',
    '掌握': '你的技能已经比较扎实，可以承担大部分测试开发工作。',
    '熟练': '你已经是一名优秀的测试开发工程师，能够独立负责项目测试平台建设。',
    '精通': '你在测试开发领域已经有很深的造诣，可以指导新人成长。',
    '专家': '你是测试开发领域的专家，在行业内有很高的水平。'
  }
  return map[overallLevel.value] || '继续努力，你会越来越优秀！'
})

const improvementTip = computed(() => {
  const score = overallScore.value
  if (score < 60) return '建议先巩固基础理论知识，多做基础练习。'
  if (score < 80) return '你的基础不错，可以开始学习进阶技能，提升综合能力。'
  return '你已经很优秀了，可以尝试更高难度的挑战，向专家方向发展。'
})

const radarOption = computed(() => {
  if (!radarData.value) return {}
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(18, 18, 31, 0.9)',
      borderColor: 'rgba(var(--tm-color-primary-rgb), 0.3)',
      textStyle: { color: TEXT_LIGHT }
    },
    legend: {
      data: ['我的能力', '行业平均'],
      bottom: 10,
      textStyle: { color: TEXT_DIM, fontSize: 12 },
      itemWidth: 16,
      itemHeight: 10
    },
    radar: {
      indicator: radarData.value.indicators,
      center: ['50%', '48%'],
      radius: '62%',
      splitNumber: 5,
      axisName: {
        color: TEXT_LIGHT,
        fontSize: 12,
        fontWeight: 500,
        formatter: (value) => value.length > 6 ? value.substring(0, 6) + '\n' + value.substring(6) : value
      },
      splitLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.15)' } },
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(var(--tm-color-primary-rgb), 0.02)',
            'rgba(var(--tm-color-primary-rgb), 0.05)',
            'rgba(var(--tm-color-primary-rgb), 0.08)',
            'rgba(var(--tm-color-primary-rgb), 0.11)',
            'rgba(var(--tm-color-primary-rgb), 0.14)'
          ]
        }
      },
      axisLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.2)' } }
    },
    series: [{
      name: '能力对比',
      type: 'radar',
      symbol: 'circle',
      symbolSize: 6,
      data: [
        {
          value: radarData.value.user_data,
          name: '我的能力',
          itemStyle: { color: PRIMARY_PURPLE },
          lineStyle: { width: 2, color: PRIMARY_PURPLE, shadowColor: 'rgba(var(--tm-color-primary-rgb), 0.6)', shadowBlur: 8 },
          areaStyle: {
            color: {
              type: 'radial',
              x: 0.5, y: 0.5, r: 0.5,
              colorStops: [
                { offset: 0, color: 'rgba(var(--tm-color-primary-rgb), 0.4)' },
                { offset: 1, color: 'rgba(var(--tm-color-primary-rgb), 0.05)' }
              ]
            }
          }
        },
        {
          value: radarData.value.industry_data,
          name: '行业平均',
          itemStyle: { color: '#64748b' },
          lineStyle: { width: 1.5, color: '#64748b', type: 'dashed' },
          areaStyle: { color: 'rgba(100, 116, 139, 0.08)' }
        }
      ]
    }]
  }
})

const barOption = computed(() => {
  const categories = skills.value.map(s => s.name)
  const values = skills.value.map(s => s.score)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(18, 18, 31, 0.9)',
      borderColor: 'rgba(var(--tm-color-primary-rgb), 0.3)',
      textStyle: { color: TEXT_LIGHT },
      formatter: (params) => `<strong>${params[0].name}</strong><br/>掌握度：<span style="color:${PRIMARY_MAGENTA};font-weight:bold">${params[0].value}%</span>`
    },
    grid: { left: '3%', right: '8%', top: '8%', bottom: '8%' },
    xAxis: {
      type: 'value', max: 100,
      axisLabel: { color: TEXT_DIM, formatter: '{value}%' },
      axisLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.08)' } }
    },
    yAxis: {
      type: 'category', data: categories,
      axisLabel: { color: TEXT_LIGHT, fontSize: 12 },
      axisLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.15)' } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: values.map((val, idx) => ({
        value: val,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: idx % 2 === 0 ? PRIMARY_PURPLE : PRIMARY_MAGENTA },
              { offset: 1, color: idx % 2 === 0 ? LIGHT_PURPLE : '#f0abfc' }
            ]
          },
          borderRadius: [0, 4, 4, 0],
          shadowColor: 'rgba(var(--tm-color-primary-rgb), 0.3)',
          shadowBlur: 6
        }
      })),
      barWidth: 18,
      label: {
        show: true, position: 'right',
        color: PRIMARY_MAGENTA, fontSize: 12, fontWeight: 'bold',
        formatter: '{c}%'
      }
    }]
  }
})

const lineOption = computed(() => {
  if (!lineData.value) return {}
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(18, 18, 31, 0.9)',
      borderColor: 'rgba(var(--tm-color-primary-rgb), 0.3)',
      textStyle: { color: TEXT_LIGHT },
      formatter: (params) => `<strong>${params[0].name}</strong><br/>综合能力：<span style="color:${PRIMARY_PURPLE};font-weight:bold">${params[0].value}分</span>`
    },
    grid: { left: '3%', right: '5%', top: '12%', bottom: '8%' },
    xAxis: {
      type: 'category', data: lineData.value.months, boundaryGap: false,
      axisLabel: { color: TEXT_DIM },
      axisLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.15)' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value', min: 40, max: 100,
      axisLabel: { color: TEXT_DIM },
      axisLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(var(--tm-color-primary-rgb), 0.08)' } }
    },
    series: [{
      name: '综合能力', type: 'line', smooth: true,
      symbol: 'circle', symbolSize: 8,
      lineStyle: { width: 3, color: PRIMARY_PURPLE, shadowColor: 'rgba(var(--tm-color-primary-rgb), 0.5)', shadowBlur: 10 },
      itemStyle: { color: PRIMARY_PURPLE, borderColor: '#12121f', borderWidth: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(var(--tm-color-primary-rgb), 0.35)' },
            { offset: 0.5, color: 'rgba(var(--tm-color-primary-rgb), 0.12)' },
            { offset: 1, color: 'rgba(var(--tm-color-primary-rgb), 0.01)' }
          ]
        }
      },
      data: lineData.value.scores
    }]
  }
})

onMounted(async () => {
  await fetchSkillData()
  await nextTick()
  animateScore(overallScore.value)
})

onBeforeUnmount(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
})

const fetchSkillData = async () => {
  loading.value = true
  try {
    const res = await request.get('/skills/radar')
    if (res.skills) skills.value = res.skills
    if (res.radar_data) radarData.value = res.radar_data
    if (res.overall_score) overallScore.value = res.overall_score
    if (res.overall_level) overallLevel.value = res.overall_level
  } catch (error) {
    console.error('获取技能数据失败，使用默认数据:', error)
  }
  try {
    const res = await request.get('/skills/progress')
    if (res.progress) {
      const months = res.progress.map(p => p.skill).slice(-6)
      const scores = res.progress.map(p => {
        if (!p.target || p.target === 0) return 0
        return Math.round((p.current || 0) / p.target * 100)
      }).slice(-6)
      if (months.length > 0) lineData.value = { months, scores }
    }
  } catch (error) {
    console.error('获取技能进度失败，使用默认数据:', error)
  }
  loading.value = false
}

const getScoreClass = (score) => {
  if (score >= 80) return 'high'
  if (score >= 60) return 'medium'
  return 'low'
}

const getScoreGradient = (score) => {
  if (score >= 80) return 'linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark))'
  if (score >= 60) return 'linear-gradient(90deg, var(--tm-color-primary), #a855f7)'
  return 'linear-gradient(90deg, #64748b, var(--tm-color-primary))'
}

const getLevelClass = (level) => {
  const map = {
    '入门': 'lv-beginner',
    '了解': 'lv-familiar',
    '掌握': 'lv-proficient',
    '熟练': 'lv-skilled',
    '精通': 'lv-expert',
    '专家': 'lv-master'
  }
  return map[level] || 'lv-familiar'
}

const getDifficultyText = (difficulty) => {
  const map = { 'easy': '简单', 'medium': '中等', 'hard': '困难' }
  return map[difficulty] || difficulty
}

const viewSkillDetail = async (skill) => {
  try {
    const res = await request.get(`/skills/detail/${skill.key}`)
    selectedSkill.value = res
    detailVisible.value = true
  } catch (error) {
    console.error('获取技能详情失败:', error)
    selectedSkill.value = skill
    detailVisible.value = true
  }
}

const goToExercise = (exerciseId) => {
  detailVisible.value = false
  router.push(`/exercises/${exerciseId}`)
}
</script>

<style scoped>
.skill-analysis-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 40px 60px;
  box-sizing: border-box;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
  gap: 36px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #27272a;
  padding-bottom: 24px;
}
.header-titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.page-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  color: #fff;
}
.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0;
}

.overall-badge {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.25);
  padding: 12px 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.badge-label {
  font-size: 12px;
  color: var(--tm-text-regular);
}
.badge-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--tm-color-primary);
}
.badge-unit {
  font-size: 14px;
  font-weight: 500;
  color: #a855f7;
}
.badge-level {
  font-size: 12px;
  font-weight: 600;
  color: #d946ef;
}

.analysis-main-content {
  display: flex;
  flex-direction: column;
  gap: 36px;
  width: 100%;
}

.dashboard-section {
  width: 100%;
  display: block;
}

.section-header {
  width: 100%;
  margin-bottom: 20px;
  text-align: left;
}
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-dot {
  color: var(--tm-color-primary);
  font-size: 12px;
  text-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.4);
}
.title-glow-line {
  width: 48px;
  height: 2px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 1px;
}

.overview-card {
  background: var(--tm-card-bg);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.12);
  border-radius: 14px;
  padding: 36px;
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
  stroke: rgba(var(--tm-color-primary-rgb), 0.1);
}
.circle-progress {
  stroke: var(--tm-color-primary);
  stroke-linecap: round;
  transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 0 6px rgba(var(--tm-color-primary-rgb), 0.6));
}
.score-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.score-num {
  font-size: 48px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}
.score-unit {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin-top: 4px;
}
.score-info h3 {
  font-size: 22px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}
.level-desc {
  font-size: 15px;
  color: var(--tm-text-regular);
  margin: 0 0 18px 0;
  line-height: 1.6;
}
.improvement-tip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.15);
  border-radius: 8px;
  font-size: 14px;
  color: #c084fc;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.chart-card-full {
  grid-column: 1 / -1;
}
.chart-card {
  background: var(--tm-card-bg);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.1);
  border-radius: 14px;
  padding: 24px;
  transition: border-color 0.3s;
}
.chart-card:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}
.chart-body {
  width: 100%;
}

.skill-cards-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%;
}

.skill-block-card {
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
}
.skill-block-card:hover {
  border-color: var(--tm-color-primary);
  box-shadow: 0 4px 20px rgba(var(--tm-color-primary-rgb), 0.06);
  transform: translateY(-2px);
}

.card-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.module-title-wrapper {
  display: flex;
  align-items: center;
  gap: 14px;
}
.module-index {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-color-primary);
  font-family: 'Courier New', monospace;
}
.module-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0;
}

.status-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.score-badge {
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
}
.score-badge.high {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  box-shadow: 0 0 12px rgba(var(--tm-color-primary-rgb), 0.3);
}
.score-badge.medium {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  box-shadow: 0 0 12px rgba(var(--tm-color-primary-rgb), 0.2);
}
.score-badge.low {
  background: linear-gradient(135deg, var(--tm-text-secondary), var(--tm-color-primary));
}

.status-tag {
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.status-tag.lv-beginner { background: rgba(148,163,184,0.12); color: #94a3b8; }
.status-tag.lv-familiar { background: rgba(251,191,36,0.12); color: #fbbf24; }
.status-tag.lv-proficient { background: rgba(52,211,153,0.12); color: #34d399; }
.status-tag.lv-skilled { background: rgba(59,130,246,0.12); color: #3b82f6; }
.status-tag.lv-expert { background: rgba(239,68,68,0.12); color: #ef4444; }
.status-tag.lv-master { background: rgba(139,92,246,0.12); color: var(--tm-color-primary); }

.card-analysis-body {
  padding-left: 34px;
}
.analysis-text {
  font-size: 14px;
  color: var(--tm-text-regular);
  line-height: 1.7;
  margin: 0;
}

.skill-progress-row {
  padding-left: 34px;
}
.skill-progress-bar {
  height: 5px;
  background: var(--tm-border-light);
  border-radius: 3px;
  overflow: hidden;
}
.skill-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-footer-tags {
  padding-left: 34px;
}
.suggestion-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.suggestion-icon { font-size: 13px; flex-shrink: 0; }
.suggestion-text {
  font-size: 13px;
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--tm-card-bg);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  padding: 40px;
}
.modal-card {
  width: 100%;
  max-width: 600px;
  background: var(--tm-card-bg);
  border: 1px solid #27272a;
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #27272a;
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0;
}
.modal-close {
  background: none;
  border: none;
  color: var(--tm-text-secondary);
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.modal-close:hover { color: var(--tm-text-primary); background: var(--bg-surface-hover); }
.modal-body { padding: 24px; }

.detail-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(var(--tm-color-primary-rgb), 0.1);
}
.detail-score {
  display: flex;
  align-items: baseline;
  flex-shrink: 0;
}
.detail-score-num {
  font-size: 56px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}
.detail-score-unit {
  font-size: 22px;
  color: var(--tm-text-regular);
  margin-left: 4px;
}
.detail-info h3 {
  font-size: 22px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}
.detail-info p {
  font-size: 14px;
  color: var(--tm-text-regular);
  margin: 0 0 12px 0;
  line-height: 1.6;
}
.detail-level-tag {
  display: inline-block;
  padding: 3px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.detail-section { margin-bottom: 24px; }
.detail-section h4 {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}
.detail-suggestion {
  padding: 16px;
  background: rgba(var(--tm-color-primary-rgb), 0.06);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.12);
  border-radius: 8px;
  line-height: 1.8;
  color: #c084fc;
  margin: 0;
  font-size: 14px;
}

.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.exercise-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(var(--tm-color-primary-rgb), 0.04);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.08);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s;
}
.exercise-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}
.exercise-info { display: flex; align-items: center; gap: 10px; }
.exercise-title { font-size: 14px; color: var(--tm-text-primary); }
.exercise-diff-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}
.exercise-diff-tag.diff-easy { background: rgba(52,211,153,0.12); color: #34d399; }
.exercise-diff-tag.diff-medium { background: rgba(251,191,36,0.12); color: #fbbf24; }
.exercise-diff-tag.diff-hard { background: rgba(248,113,113,0.12); color: #f87171; }
.exercise-time { font-size: 12px; color: var(--tm-text-secondary); }

@media (max-width: 1200px) {
  .charts-grid { grid-template-columns: 1fr; }
  .score-section { flex-direction: column; gap: 30px; text-align: center; }
  .skill-analysis-container { padding: 32px 24px; }
}

@media (max-width: 768px) {
  .analysis-header { flex-direction: column; align-items: flex-start; gap: 16px; }
  .skill-analysis-container { padding: 24px 16px; }
}
</style>