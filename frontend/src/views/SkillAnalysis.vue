<template>
  <div class="skill-analysis">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">技能分析中心</h1>
        <p class="page-subtitle">全面了解你的测试开发技能掌握情况，针对性提升</p>
      </div>

      <div class="overview-card">
        <div class="score-section">
          <div class="score-circle">
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
                :stroke-dashoffset="251.2 - (251.2 * animatedScore / 100)"
              />
            </svg>
            <div class="score-content">
              <div class="score-number">{{ Math.round(animatedScore) }}</div>
              <div class="score-label">综合得分</div>
              <div class="score-level">{{ overallLevel }}</div>
            </div>
          </div>
          <div class="score-info">
            <h2>能力评估</h2>
            <p class="level-desc">{{ levelDescription }}</p>
            <div class="improvement-tip">
              <el-icon size="20" color="#d946ef"><Warning /></el-icon>
              <span>{{ improvementTip }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="content-grid">
        <div class="left-section">
          <div class="card">
            <h3 class="card-title">
              <span class="title-icon">◈</span>
              技能雷达图
            </h3>
            <div class="chart-container" ref="radarChartRef">
              <v-chart
                :option="radarOption"
                :autoresize="true"
                style="width: 100%; height: 350px;"
              />
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">
              <span class="title-icon">◈</span>
              技能提升进度
            </h3>
            <div class="chart-container" ref="lineChartRef">
              <v-chart
                :option="lineOption"
                :autoresize="true"
                style="width: 100%; height: 350px;"
              />
            </div>
          </div>
        </div>

        <div class="right-section">
          <div class="card">
            <h3 class="card-title">
              <span class="title-icon">◈</span>
              技术栈掌握度
            </h3>
            <div class="chart-container" ref="barChartRef">
              <v-chart
                :option="barOption"
                :autoresize="true"
                style="width: 100%; height: 350px;"
              />
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">
              <span class="title-icon">◈</span>
              技能详情
            </h3>
            <div class="skills-list">
              <div
                class="skill-item"
                v-for="skill in skills"
                :key="skill.key"
                @click="viewSkillDetail(skill)"
              >
                <div class="skill-header">
                  <div class="skill-info">
                    <h4 class="skill-name">{{ skill.name }}</h4>
                    <p class="skill-desc">{{ skill.description }}</p>
                  </div>
                  <div class="skill-score">
                    <div class="score-badge" :class="getScoreClass(skill.score)">
                      {{ skill.score }}分
                    </div>
                    <el-tag :type="getLevelTagType(skill.level)" size="small" effect="dark">
                      {{ skill.level }}
                    </el-tag>
                  </div>
                </div>
                <div class="skill-progress-bar">
                  <div
                    class="skill-progress-fill"
                    :style="{ width: skill.score + '%', background: getScoreGradient(skill.score) }"
                  ></div>
                </div>
                <p class="skill-suggestion">
                  <el-icon size="14" color="#8b5cf6"><InfoFilled /></el-icon>
                  {{ skill.suggestion }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <el-dialog
        v-model="detailVisible"
        title="技能详情"
        width="600px"
        class="skill-detail-dialog"
      >
        <div v-if="selectedSkill" class="skill-detail-content">
          <div class="detail-header">
            <div class="detail-score">
              <div class="score-number-lg">{{ selectedSkill.score }}</div>
              <div class="score-unit">分</div>
            </div>
            <div class="detail-info">
              <h3>{{ selectedSkill.name }}</h3>
              <p>{{ selectedSkill.description }}</p>
              <el-tag :type="getLevelTagType(selectedSkill.level)" size="large" effect="dark">
                {{ selectedSkill.level }}
              </el-tag>
            </div>
          </div>

          <div class="detail-section">
            <h4>提升建议</h4>
            <p class="suggestion-text">{{ selectedSkill.suggestion }}</p>
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
                  <el-tag size="small" :type="getDifficultyTagType(ex.difficulty)" effect="dark">
                    {{ getDifficultyText(ex.difficulty) }}
                  </el-tag>
                </div>
                <span class="exercise-time">{{ ex.time_estimate }}分钟</span>
              </div>
            </div>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, InfoFilled } from '@element-plus/icons-vue'
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

const PRIMARY_PURPLE = '#8b5cf6'
const PRIMARY_MAGENTA = '#d946ef'
const MID_PURPLE = '#a855f7'
const LIGHT_PURPLE = '#c084fc'
const BG_DEEP = '#0a0a14'
const BG_SURFACE = '#12121f'
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

const DEFAULT_BAR_DATA = {
  categories: ['Pytest', 'Requests/AIOHTTP', 'FastAPI', 'Docker/Nginx', 'Vue3/ElementPlus', 'Jenkins/GitLabCI', 'Allure/报告', 'SQL/Redis'],
  values: [85, 90, 78, 75, 72, 70, 82, 68]
}

const DEFAULT_LINE_DATA = {
  months: ['10月', '11月', '12月', '1月', '2月', '3月'],
  scores: [58, 63, 68, 72, 76, 82]
}

const skills = ref(DEFAULT_SKILLS)
const radarData = ref(DEFAULT_RADAR_DATA)
const barData = ref(DEFAULT_BAR_DATA)
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
  const startValue = 0

  const step = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedScore.value = startValue + (target - startValue) * eased

    if (progress < 1) {
      animationFrameId = requestAnimationFrame(step)
    }
  }

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  animationFrameId = requestAnimationFrame(step)
}

const levelDescription = computed(() => {
  const level = overallLevel.value
  const descriptions = {
    '入门': '你刚刚进入测试开发领域，还有很大的提升空间，加油！',
    '了解': '你已经掌握了基础的测试开发知识，可以尝试更多实战练习。',
    '掌握': '你的技能已经比较扎实，可以承担大部分测试开发工作。',
    '熟练': '你已经是一名优秀的测试开发工程师，能够独立负责项目测试平台建设。',
    '精通': '你在测试开发领域已经有很深的造诣，可以指导新人成长。',
    '专家': '你是测试开发领域的专家，在行业内有很高的水平。'
  }
  return descriptions[level] || '继续努力，你会越来越优秀！'
})

const improvementTip = computed(() => {
  const score = overallScore.value
  if (score < 60) {
    return '建议先巩固基础理论知识，多做基础练习。'
  } else if (score < 80) {
    return '你的基础不错，可以开始学习进阶技能，提升综合能力。'
  } else {
    return '你已经很优秀了，可以尝试更高难度的挑战，向专家方向发展。'
  }
})

const radarOption = computed(() => {
  if (!radarData.value) return {}
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(18, 18, 31, 0.9)',
      borderColor: 'rgba(139, 92, 246, 0.3)',
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
        formatter: (value) => {
          if (value.length > 6) {
            return value.substring(0, 6) + '\n' + value.substring(6)
          }
          return value
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(139, 92, 246, 0.15)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(139, 92, 246, 0.02)',
            'rgba(139, 92, 246, 0.05)',
            'rgba(139, 92, 246, 0.08)',
            'rgba(139, 92, 246, 0.11)',
            'rgba(139, 92, 246, 0.14)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(139, 92, 246, 0.2)'
        }
      }
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
          lineStyle: {
            width: 2,
            color: PRIMARY_PURPLE,
            shadowColor: 'rgba(139, 92, 246, 0.6)',
            shadowBlur: 8
          },
          areaStyle: {
            color: {
              type: 'radial',
              x: 0.5,
              y: 0.5,
              r: 0.5,
              colorStops: [
                { offset: 0, color: 'rgba(139, 92, 246, 0.4)' },
                { offset: 1, color: 'rgba(139, 92, 246, 0.05)' }
              ]
            }
          }
        },
        {
          value: radarData.value.industry_data,
          name: '行业平均',
          itemStyle: { color: '#64748b' },
          lineStyle: {
            width: 1.5,
            color: '#64748b',
            type: 'dashed'
          },
          areaStyle: {
            color: 'rgba(100, 116, 139, 0.08)'
          }
        }
      ]
    }]
  }
})

const barOption = computed(() => {
  if (!barData.value) return {}
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(18, 18, 31, 0.9)',
      borderColor: 'rgba(139, 92, 246, 0.3)',
      textStyle: { color: TEXT_LIGHT },
      formatter: (params) => {
        const item = params[0]
        return `<strong>${item.name}</strong><br/>掌握度：<span style="color:${PRIMARY_MAGENTA};font-weight:bold">${item.value}%</span>`
      }
    },
    grid: {
      left: '3%',
      right: '8%',
      top: '8%',
      bottom: '8%'
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        color: TEXT_DIM,
        formatter: '{value}%'
      },
      axisLine: { lineStyle: { color: 'rgba(139, 92, 246, 0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(139, 92, 246, 0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: barData.value.categories,
      axisLabel: {
        color: TEXT_LIGHT,
        fontSize: 12
      },
      axisLine: { lineStyle: { color: 'rgba(139, 92, 246, 0.15)' } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: barData.value.values.map((val, idx) => ({
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
          shadowColor: 'rgba(139, 92, 246, 0.3)',
          shadowBlur: 6
        }
      })),
      barWidth: 18,
      label: {
        show: true,
        position: 'right',
        color: PRIMARY_MAGENTA,
        fontSize: 12,
        fontWeight: 'bold',
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
      borderColor: 'rgba(139, 92, 246, 0.3)',
      textStyle: { color: TEXT_LIGHT },
      formatter: (params) => {
        const item = params[0]
        return `<strong>${item.name}</strong><br/>综合能力：<span style="color:${PRIMARY_PURPLE};font-weight:bold">${item.value}分</span>`
      }
    },
    grid: {
      left: '3%',
      right: '5%',
      top: '12%',
      bottom: '8%'
    },
    xAxis: {
      type: 'category',
      data: lineData.value.months,
      boundaryGap: false,
      axisLabel: { color: TEXT_DIM },
      axisLine: { lineStyle: { color: 'rgba(139, 92, 246, 0.15)' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      min: 40,
      max: 100,
      axisLabel: { color: TEXT_DIM },
      axisLine: { lineStyle: { color: 'rgba(139, 92, 246, 0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(139, 92, 246, 0.08)' } }
    },
    series: [{
      name: '综合能力',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: PRIMARY_PURPLE,
        shadowColor: 'rgba(139, 92, 246, 0.5)',
        shadowBlur: 10
      },
      itemStyle: {
        color: PRIMARY_PURPLE,
        borderColor: BG_SURFACE,
        borderWidth: 2
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(139, 92, 246, 0.35)' },
            { offset: 0.5, color: 'rgba(139, 92, 246, 0.12)' },
            { offset: 1, color: 'rgba(139, 92, 246, 0.01)' }
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
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
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
      const scores = res.progress.map(p => Math.round(p.current / p.target * 100)).slice(-6)
      if (months.length > 0) {
        lineData.value = { months, scores }
      }
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
  if (score >= 80) return 'linear-gradient(90deg, #8b5cf6, #d946ef)'
  if (score >= 60) return 'linear-gradient(90deg, #8b5cf6, #a855f7)'
  return 'linear-gradient(90deg, #64748b, #8b5cf6)'
}

const getLevelTagType = (level) => {
  const map = {
    '入门': 'info',
    '了解': 'warning',
    '掌握': 'success',
    '熟练': 'primary',
    '精通': 'danger',
    '专家': 'danger'
  }
  return map[level] || 'info'
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    'easy': 'success',
    'medium': 'warning',
    'hard': 'danger'
  }
  return map[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const map = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  }
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
.skill-analysis {
  padding: 30px 0;
  min-height: calc(100vh - 60px);
  background-color: var(--tm-bg-page);
  background-image: radial-gradient(ellipse at 20% 50%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(217, 70, 239, 0.04) 0%, transparent 50%);
  background-size: cover;
  background-position: center;
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
  text-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
}

.page-subtitle {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0;
}

.overview-card {
  background: var(--tm-bg-card);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1),
              0 0 40px rgba(139, 92, 246, 0.05),
              inset 0 1px 0 rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  margin-bottom: 30px;
  transition: box-shadow 0.3s ease;
}

.overview-card:hover {
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15),
              0 0 60px rgba(139, 92, 246, 0.08),
              inset 0 1px 0 rgba(139, 92, 246, 0.15);
}

.score-section {
  display: flex;
  align-items: center;
  gap: 60px;
}

.score-circle {
  position: relative;
  width: 200px;
  height: 200px;
  flex-shrink: 0;
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
  stroke: url(#scoreGradient);
  stroke: var(--tm-color-primary, #8b5cf6);
  stroke-linecap: round;
  transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 0 6px rgba(139, 92, 246, 0.6));
}

.score-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-number {
  font-size: 56px;
  font-weight: 900;
  background: var(--tm-gradient-brand, linear-gradient(135deg, #8b5cf6, #d946ef));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 4px;
  font-variant-numeric: tabular-nums;
}

.score-label {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 4px;
  letter-spacing: 2px;
}

.score-level {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-color-primary-dark, #d946ef);
  text-shadow: 0 0 10px rgba(217, 70, 239, 0.4);
}

.score-info h2 {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.level-desc {
  font-size: 16px;
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
  line-height: 1.6;
}

.improvement-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(217, 70, 239, 0.08);
  border: 1px solid rgba(217, 70, 239, 0.15);
  border-radius: 8px;
  font-size: 14px;
  color: var(--tm-color-primary-dark, #d946ef);
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.card {
  background: var(--tm-bg-card);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1),
              0 0 40px rgba(139, 92, 246, 0.03);
  border: 1px solid rgba(139, 92, 246, 0.12);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  margin-bottom: 0;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}

.card:hover {
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15),
              0 0 60px rgba(139, 92, 246, 0.06);
  border-color: rgba(139, 92, 246, 0.2);
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: var(--tm-color-primary, #8b5cf6);
  font-size: 14px;
  text-shadow: 0 0 8px rgba(139, 92, 246, 0.5);
}

.chart-container {
  width: 100%;
  height: 350px;
}

.left-section {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.right-section {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skill-item {
  padding: 16px;
  background: rgba(139, 92, 246, 0.04);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(139, 92, 246, 0.08);
}

.skill-item:hover {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.2);
  transform: translateX(4px);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.1);
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.skill-info {
  flex: 1;
  margin-right: 20px;
}

.skill-name {
  font-size: 15px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 4px 0;
}

.skill-desc {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.skill-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.score-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 16px;
  font-weight: bold;
  color: white;
}

.score-badge.high {
  background: var(--tm-gradient-brand, linear-gradient(135deg, #8b5cf6, #d946ef));
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
}

.score-badge.medium {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.3);
}

.score-badge.low {
  background: linear-gradient(135deg, #64748b, #8b5cf6);
  box-shadow: 0 0 12px rgba(100, 116, 139, 0.3);
}

.skill-progress-bar {
  height: 4px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.skill-progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
}

.skill-suggestion {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin: 0;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.skill-detail-content {
  padding: 10px 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.detail-score {
  display: flex;
  align-items: baseline;
  flex-shrink: 0;
}

.score-number-lg {
  font-size: 64px;
  font-weight: 900;
  background: var(--tm-gradient-brand, linear-gradient(135deg, #8b5cf6, #d946ef));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.score-unit {
  font-size: 24px;
  color: var(--tm-text-secondary);
  margin-left: 4px;
}

.detail-info h3 {
  font-size: 24px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 8px 0;
}

.detail-info p {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 16px;
  font-weight: bold;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.suggestion-text {
  padding: 16px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 8px;
  line-height: 1.8;
  color: var(--tm-color-primary-light, #c084fc);
  margin: 0;
}

.exercise-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exercise-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.04);
  border: 1px solid rgba(139, 92, 246, 0.08);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.exercise-item:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
}

.exercise-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.exercise-title {
  font-size: 14px;
  color: var(--tm-text-primary);
}

.exercise-time {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .score-section {
    flex-direction: column;
    gap: 30px;
    text-align: center;
  }

  .improvement-tip {
    justify-content: center;
  }
}
</style>
