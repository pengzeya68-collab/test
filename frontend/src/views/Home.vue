<template>
  <div class="home-page">
    <section class="hero" aria-labelledby="home-title">
      <div class="hero-copy">
        <p class="eyebrow">TESTMASTER QUALITY ENGINEERING</p>
        <h1 id="home-title">把测试能力，沉淀为可交付的工程实践</h1>
        <p class="hero-description">
          从系统化学习到接口、UI 与性能自动化，在同一个平台持续构建、验证和复盘测试能力。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="goToLearningPaths">
            开始学习
            <el-icon><ArrowRight /></el-icon>
          </el-button>
          <el-button size="large" @click="goToAutomation">进入自动化工作台</el-button>
        </div>
      </div>

      <div class="hero-overview" aria-label="能力成长路径">
        <div class="overview-header">
          <span>能力成长路径</span>
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div v-for="item in capabilityFlow" :key="item.title" class="overview-row">
          <div class="overview-icon"><el-icon><component :is="item.icon" /></el-icon></div>
          <div>
            <strong>{{ item.title }}</strong>
            <span>{{ item.description }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="path-title">
      <div class="section-heading">
        <div>
          <p class="section-kicker">LEARNING PATHS</p>
          <h2 id="path-title">一条清晰的成长路径</h2>
        </div>
        <el-button link type="primary" @click="goToLearningPaths">查看全部路径 <el-icon><ArrowRight /></el-icon></el-button>
      </div>

      <div class="path-grid">
        <article v-for="stage in stages" :key="stage.id" class="path-card" tabindex="0" @click="viewStagePaths(stage.id)" @keyup.enter="viewStagePaths(stage.id)">
          <div class="path-icon"><el-icon><component :is="stage.icon" /></el-icon></div>
          <div class="path-content">
            <div class="path-meta"><span>{{ stage.duration }}</span><span>{{ stage.target }}</span></div>
            <h3>{{ stage.title }}</h3>
            <p>{{ stage.description }}</p>
          </div>
          <el-icon class="path-arrow"><ArrowRight /></el-icon>
        </article>
      </div>
    </section>

    <section class="section" aria-labelledby="tool-title">
      <div class="section-heading">
        <div>
          <p class="section-kicker">TESTING WORKBENCH</p>
          <h2 id="tool-title">从练习走向真实测试交付</h2>
        </div>
      </div>

      <div class="workbench-grid">
        <article v-for="tool in workbenches" :key="tool.title" class="workbench-card" @click="goTo(tool.path)">
          <div class="workbench-icon"><el-icon><component :is="tool.icon" /></el-icon></div>
          <div class="workbench-content">
            <p class="workbench-tag">{{ tool.tag }}</p>
            <h3>{{ tool.title }}</h3>
            <p>{{ tool.description }}</p>
            <span class="workbench-link">进入工作台 <el-icon><ArrowRight /></el-icon></span>
          </div>
        </article>
      </div>
    </section>

    <section v-if="isLoggedIn" class="section personal-section" aria-labelledby="progress-title">
      <div class="section-heading">
        <div>
          <p class="section-kicker">MY PROGRESS</p>
          <h2 id="progress-title">我的学习进度</h2>
        </div>
        <el-button link type="primary" @click="goTo('/skill-analysis')">查看技能分析 <el-icon><ArrowRight /></el-icon></el-button>
      </div>

      <div class="stats-grid">
        <article v-for="stat in stats" :key="stat.label" class="stat-card" @click="goTo(stat.path)">
          <div class="stat-icon"><el-icon><component :is="stat.icon" /></el-icon></div>
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </article>
      </div>

      <div v-if="inProgressPaths.length" class="continue-panel">
        <div class="continue-header">
          <div>
            <h3>继续学习</h3>
            <p>从上次进度继续，不中断你的学习节奏。</p>
          </div>
          <el-button link type="primary" @click="goToLearningPaths">学习路径 <el-icon><ArrowRight /></el-icon></el-button>
        </div>
        <div class="continue-list">
          <button v-for="item in inProgressPaths" :key="item.pathId" class="continue-item" type="button" @click="goTo(`/learning-paths/${item.pathId}`)">
            <span class="continue-name">{{ item.title }}</span>
            <span class="continue-status">{{ item.completed }}/{{ item.total }} 题</span>
            <span class="progress-track"><i :style="{ width: `${item.progress}%` }" /></span>
            <span class="continue-progress">{{ item.progress }}%</span>
          </button>
        </div>
      </div>
    </section>

    <section class="value-grid" aria-label="平台能力">
      <article v-for="value in platformValues" :key="value.title" class="value-item">
        <el-icon><component :is="value.icon" /></el-icon>
        <div><h3>{{ value.title }}</h3><p>{{ value.description }}</p></div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  DataLine,
  EditPen,
  Guide,
  Monitor,
  Notebook,
  Odometer,
  OfficeBuilding,
  Reading,
  Setting,
  TrendCharts,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn)
const dashboard = ref({ score: '-', level: '尚未测评', exercises: 0, achievements: 0 })
const inProgressPaths = ref([])

const capabilityFlow = [
  { title: '系统学习', description: '掌握测试基础与方法', icon: Reading },
  { title: '实战训练', description: '用习题与项目巩固能力', icon: EditPen },
  { title: '质量交付', description: '完成自动化与回归验证', icon: Setting },
]

const stages = [
  { id: 1, title: '测试入门筑基', description: '建立测试思维，掌握基础理论和测试方法。', duration: '4 周', target: '测试实习生', icon: Reading },
  { id: 2, title: '功能测试精通', description: '独立完成 Web、App 与小程序等项目测试。', duration: '8 周', target: '初级测试工程师', icon: EditPen },
  { id: 3, title: '测试技术进阶', description: '掌握接口、自动化与性能测试的核心方法。', duration: '12 周', target: '中级测试工程师', icon: TrendCharts },
  { id: 4, title: '自动化测试专家', description: '搭建自动化体系，沉淀稳定的回归资产。', duration: '16 周', target: '高级测试工程师', icon: Odometer },
  { id: 5, title: '测试架构师之路', description: '构建测试平台、质量体系与效能度量能力。', duration: '20 周+', target: '测试专家', icon: OfficeBuilding },
]

const workbenches = [
  { tag: 'API & SCENARIO', title: '接口与场景自动化', description: '设计接口用例，编排跨服务场景，并在不同环境中执行回归。', path: '/auto-test', icon: DataLine },
  { tag: 'UI AUTOMATION', title: 'UI 自动化回归', description: '录制、编辑和调试真实浏览器操作，维护可重复执行的 UI 回归套件。', path: '/ui-automation/cases', icon: Monitor },
  { tag: 'TEST TOOLKIT', title: '测试效率工具', description: '集中使用测试数据、Mock、性能与测试辅助工具，提升交付效率。', path: '/tools', icon: Guide },
]

const platformValues = [
  { title: '体系化课程', description: '覆盖测试基础、专项能力和工程实践。', icon: Notebook },
  { title: '实战习题', description: '在练习中巩固方法和质量判断能力。', icon: EditPen },
  { title: '进度跟踪', description: '清楚了解学习状态与待提升方向。', icon: TrendCharts },
  { title: '自动化工具', description: '把测试设计转化为可执行的回归资产。', icon: Setting },
]

const stats = computed(() => [
  { label: '综合得分', value: dashboard.value.score, path: '/skill-analysis', icon: TrendCharts },
  { label: '能力等级', value: dashboard.value.level, path: '/skill-analysis', icon: Odometer },
  { label: '完成习题', value: dashboard.value.exercises, path: '/exercises', icon: EditPen },
  { label: '获得成就', value: dashboard.value.achievements, path: '/profile', icon: Notebook },
])

const goTo = (path) => router.push(path)
const goToLearningPaths = () => goTo('/learning-paths')
const goToAutomation = () => goTo('/auto-test')
const viewStagePaths = (stageId) => router.push({ path: '/learning-paths', query: { stage: stageId } })

const loadDashboard = async () => {
  if (!isLoggedIn.value) return
  const [skillsResult, achievementsResult, progressResult, pathsResult] = await Promise.allSettled([
    request.get('/skills/radar'),
    request.get('/achievements'),
    request.get('/learning-paths/all-progress'),
    request.get('/learning-paths'),
  ])

  if (skillsResult.status === 'fulfilled') {
    const result = skillsResult.value || {}
    dashboard.value.score = result.overall_score ?? '-'
    dashboard.value.level = result.overall_level || '尚未测评'
    dashboard.value.exercises = result.exercises_done || 0
  }
  if (achievementsResult.status === 'fulfilled') {
    dashboard.value.achievements = achievementsResult.value?.unlocked_count || 0
  }
  if (progressResult.status !== 'fulfilled') return

  const paths = pathsResult.status === 'fulfilled'
    ? (Array.isArray(pathsResult.value) ? pathsResult.value : pathsResult.value?.items || [])
    : []
  const names = new Map(paths.map(path => [path.id, path.title]))
  const progressItems = progressResult.value?.progress || []
  inProgressPaths.value = progressItems
    .filter(item => item.completed_exercises > 0 && item.progress_percent < 100)
    .sort((left, right) => right.progress_percent - left.progress_percent)
    .slice(0, 3)
    .map(item => ({
      pathId: item.path_id,
      title: names.get(item.path_id) || `学习路径 #${item.path_id}`,
      completed: item.completed_exercises,
      total: item.total_exercises,
      progress: item.progress_percent,
    }))
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.home-page {
  width: 100%;
  min-height: 100%;
  padding: 40px clamp(20px, 4vw, 64px) 56px;
  background: var(--tm-bg-page);
  color: var(--tm-text-primary);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(290px, 0.65fr);
  gap: clamp(28px, 5vw, 72px);
  align-items: center;
  min-height: 350px;
  padding: clamp(30px, 5vw, 64px);
  overflow: hidden;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--tm-shadow-card);
}

.eyebrow, .section-kicker, .workbench-tag {
  margin: 0 0 12px;
  color: var(--tm-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.hero h1 {
  max-width: 760px;
  margin: 0;
  color: var(--tm-text-primary);
  font-size: clamp(32px, 4vw, 52px);
  font-weight: 800;
  letter-spacing: 0;
  line-height: 1.18;
}

.hero-description {
  max-width: 650px;
  margin: 20px 0 28px;
  color: var(--tm-text-regular);
  font-size: 16px;
  line-height: 1.8;
}

.hero-actions, .section-heading, .continue-header { display: flex; align-items: center; }
.hero-actions { gap: 12px; flex-wrap: wrap; }
.hero-actions :deep(.el-button) { margin: 0; }
.hero-actions :deep(.el-icon), .section-heading :deep(.el-icon), .continue-header :deep(.el-icon), .workbench-link :deep(.el-icon) { margin-left: 6px; }

.hero-overview {
  padding: 20px;
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
  border-radius: var(--radius-md);
}

.overview-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 4px 14px; color: var(--tm-text-primary); font-size: 14px; font-weight: 700; }
.overview-header .el-icon { color: var(--tm-color-primary); font-size: 20px; }
.overview-row { display: flex; gap: 12px; align-items: center; padding: 14px 4px; border-top: 1px solid var(--tm-border-light); }
.overview-icon, .path-icon, .workbench-icon, .stat-icon { display: grid; flex: 0 0 auto; place-items: center; color: var(--tm-color-primary); background: rgba(var(--tm-color-primary-rgb), 0.14); }
.overview-icon { width: 36px; height: 36px; border-radius: var(--radius-sm); }
.overview-row strong, .overview-row span { display: block; }
.overview-row strong { color: var(--tm-text-primary); font-size: 14px; }
.overview-row span { margin-top: 3px; color: var(--tm-text-secondary); font-size: 12px; }

.section { margin-top: 56px; }
.section-heading { justify-content: space-between; gap: 24px; margin-bottom: 22px; }
.section-kicker { margin-bottom: 8px; }
.section-heading h2 { margin: 0; color: var(--tm-text-primary); font-size: 24px; font-weight: 750; letter-spacing: 0; }

.path-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }
.path-card { display: flex; flex-direction: column; min-height: 260px; padding: 22px; cursor: pointer; background: var(--tm-card-bg); border: 1px solid var(--tm-border-light); border-radius: var(--radius-md); transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease; }
.path-card:hover, .path-card:focus-visible { outline: none; border-color: rgba(var(--tm-color-primary-rgb), 0.45); box-shadow: var(--tm-shadow-hover); transform: translateY(-2px); }
.path-icon { width: 42px; height: 42px; margin-bottom: 20px; border-radius: var(--radius-sm); font-size: 21px; }
.path-content { flex: 1; }
.path-meta { display: flex; justify-content: space-between; gap: 8px; color: var(--tm-text-secondary); font-size: 11px; }
.path-card h3 { margin: 12px 0 8px; color: var(--tm-text-primary); font-size: 16px; line-height: 1.4; }
.path-card p { margin: 0; color: var(--tm-text-regular); font-size: 13px; line-height: 1.65; }
.path-arrow { align-self: flex-end; margin-top: 20px; color: var(--tm-color-primary); }

.workbench-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.workbench-card { display: flex; gap: 18px; min-height: 205px; padding: 26px; cursor: pointer; background: var(--tm-card-bg); border: 1px solid var(--tm-border-light); border-radius: var(--radius-md); transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease; }
.workbench-card:hover { border-color: rgba(var(--tm-color-primary-rgb), 0.45); box-shadow: var(--tm-shadow-hover); transform: translateY(-2px); }
.workbench-icon { width: 44px; height: 44px; border-radius: var(--radius-sm); font-size: 22px; }
.workbench-content { display: flex; flex: 1; flex-direction: column; align-items: flex-start; }
.workbench-tag { margin-bottom: 7px; font-size: 10px; }
.workbench-card h3 { margin: 0; color: var(--tm-text-primary); font-size: 17px; }
.workbench-card p:not(.workbench-tag) { margin: 10px 0 18px; color: var(--tm-text-regular); font-size: 13px; line-height: 1.65; }
.workbench-link { display: inline-flex; align-items: center; margin-top: auto; color: var(--tm-color-primary); font-size: 13px; font-weight: 600; }

.personal-section { padding: 30px; background: var(--tm-card-bg); border: 1px solid var(--tm-border-light); border-radius: var(--radius-lg); }
.personal-section .section-heading { margin-bottom: 24px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.stat-card { display: flex; flex-direction: column; min-height: 150px; padding: 20px; cursor: pointer; background: rgba(var(--tm-color-primary-rgb), 0.06); border: 1px solid var(--tm-border-light); border-radius: var(--radius-md); transition: background 0.2s ease, transform 0.2s ease; }
.stat-card:hover { background: rgba(var(--tm-color-primary-rgb), 0.12); transform: translateY(-2px); }
.stat-icon { width: 34px; height: 34px; border-radius: var(--radius-sm); font-size: 17px; }
.stat-value { margin-top: auto; overflow: hidden; color: var(--tm-text-primary); font-size: 25px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
.stat-label { margin-top: 5px; color: var(--tm-text-secondary); font-size: 13px; }

.continue-panel { margin-top: 26px; padding-top: 26px; border-top: 1px solid var(--tm-border-light); }
.continue-header { justify-content: space-between; gap: 16px; }
.continue-header h3 { margin: 0; color: var(--tm-text-primary); font-size: 17px; }
.continue-header p { margin: 5px 0 0; color: var(--tm-text-secondary); font-size: 13px; }
.continue-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
.continue-item { display: grid; grid-template-columns: 1fr auto; gap: 7px 10px; padding: 15px; cursor: pointer; color: inherit; text-align: left; background: transparent; border: 1px solid var(--tm-border-light); border-radius: var(--radius-md); }
.continue-item:hover { border-color: rgba(var(--tm-color-primary-rgb), 0.45); }
.continue-name { overflow: hidden; color: var(--tm-text-primary); font-size: 14px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.continue-status, .continue-progress { color: var(--tm-text-secondary); font-size: 12px; }
.continue-progress { color: var(--tm-color-primary); text-align: right; }
.progress-track { grid-column: 1 / -1; height: 6px; overflow: hidden; background: var(--tm-border-light); border-radius: 99px; }
.progress-track i { display: block; height: 100%; background: var(--tm-color-primary); border-radius: inherit; }

.value-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; margin-top: 56px; }
.value-item { display: flex; gap: 13px; align-items: flex-start; padding: 6px; }
.value-item > .el-icon { flex: 0 0 auto; margin-top: 2px; color: var(--tm-color-primary); font-size: 21px; }
.value-item h3 { margin: 0; color: var(--tm-text-primary); font-size: 14px; }
.value-item p { margin: 6px 0 0; color: var(--tm-text-secondary); font-size: 12px; line-height: 1.6; }

@media (max-width: 1220px) {
  .path-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .path-card { min-height: 225px; }
  .workbench-grid { grid-template-columns: 1fr; }
  .workbench-card { min-height: 150px; }
}

@media (max-width: 820px) {
  .home-page { padding: 24px 16px 40px; }
  .hero { grid-template-columns: 1fr; min-height: auto; padding: 28px 22px; }
  .hero h1 { font-size: 32px; }
  .section { margin-top: 40px; }
  .stats-grid, .value-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .continue-list { grid-template-columns: 1fr; }
}

@media (max-width: 560px) {
  .section-heading { align-items: flex-end; }
  .section-heading h2 { font-size: 21px; }
  .section-heading :deep(.el-button) { padding-right: 0; }
  .path-grid, .stats-grid, .value-grid { grid-template-columns: 1fr; }
  .path-card { min-height: 190px; }
  .hero-actions { display: grid; grid-template-columns: 1fr; }
  .hero-actions :deep(.el-button) { width: 100%; }
  .personal-section { padding: 22px 16px; }
  .workbench-card { padding: 20px; }
}
</style>
