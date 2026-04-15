<template>
  <div class="home">
    <!-- 英雄区 -->
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">TestMaster <span class="hero-title-sub">测试工程师成长平台</span></h1>
          <p class="hero-subtitle">从小白到测试架构师的完整学习路径，一站式提升测试能力</p>
          <div class="hero-buttons">
            <el-button class="btn-primary" size="large" @click="goToLearningPaths">
              开始学习
            </el-button>
            <el-button class="btn-secondary" size="large" @click="goToExercises">
              习题练习
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 学习路径阶段展示 -->
    <section class="section">
      <div class="container">
        <h2 class="section-title">
          <span class="title-text">5大学习阶段，循序渐进</span>
          <span class="title-underline"></span>
        </h2>
        <div class="stage-grid">
          <el-card class="stage-card" v-for="stage in stages" :key="stage.id" shadow="hover">
            <div class="stage-inner">
              <div class="stage-icon" :style="{ backgroundColor: stage.color }">
                <span class="icon-text">{{ stage.icon }}</span>
              </div>
              <h3 class="stage-title">{{ stage.title }}</h3>
              <p class="stage-desc">{{ stage.desc }}</p>
              <div class="stage-info">
                <el-tag size="small" type="info">{{ stage.duration }}</el-tag>
                <span class="stage-target">{{ stage.target }}</span>
              </div>
              <el-button
                type="primary"
                text
                class="stage-button"
                @click="viewStagePaths(stage.id)"
              >
                探索学习路线 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </el-card>
        </div>
      </div>
    </section>

    <!-- 专项练习 -->
    <section class="section section-bg-light">
      <div class="container">
        <h2 class="section-title">
          <span class="title-text">专项练习专区</span>
          <span class="title-underline"></span>
        </h2>
        <div class="module-grid">
          <div class="module-card" @click="goToModule('automation')">
            <span class="module-icon">🤖</span>
            <h3 class="module-title">自动化测试</h3>
            <p class="module-desc">Selenium、Appium、Playwright、Cypress 自动化测试实战习题</p>
            <el-button type="primary" text class="module-button">
              开始练习 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
          <div class="module-card" @click="goToModule('api')">
            <span class="module-icon">🌐</span>
            <h3 class="module-title">接口调试 & 自动化</h3>
            <p class="module-desc">在线接口调试、自动化测试场景编排、定时任务调度</p>
            <el-button type="primary" text class="module-button">
              开始使用 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 学习仪表盘（已登录用户） -->
    <section class="section" v-if="userStore.isLoggedIn">
      <div class="container">
        <h2 class="section-title">
          <span class="title-text">我的学习仪表盘</span>
          <span class="title-underline"></span>
        </h2>
        <div class="dashboard-grid">
          <div class="dash-card dash-score" @click="router.push('/skill-analysis')">
            <div class="dash-icon">📊</div>
            <div class="dash-value">{{ dashboardData.overallScore || '--' }}</div>
            <div class="dash-label">综合得分</div>
            <div class="dash-level">{{ dashboardData.overallLevel || '未测评' }}</div>
          </div>
          <div class="dash-card dash-exercises" @click="router.push('/exercises')">
            <div class="dash-icon">✏️</div>
            <div class="dash-value">{{ dashboardData.exercisesDone }}</div>
            <div class="dash-label">完成习题</div>
            <div class="dash-sub">继续刷题 →</div>
          </div>
          <div class="dash-card dash-interview" @click="router.push('/interview')">
            <div class="dash-icon">🎤</div>
            <div class="dash-value">{{ dashboardData.interviewsDone }}</div>
            <div class="dash-label">模拟面试</div>
            <div class="dash-sub">模拟实战 →</div>
          </div>
          <div class="dash-card dash-achievements" @click="router.push('/profile')">
            <div class="dash-icon">🏆</div>
            <div class="dash-value">{{ dashboardData.achievementsUnlocked }}</div>
            <div class="dash-label">成就徽章</div>
            <div class="dash-sub">查看全部 →</div>
          </div>
        </div>

        <!-- 继续学习快速入口 -->
        <div class="continue-section" v-if="inProgressPaths.length > 0">
          <h3 class="continue-title">📖 继续学习</h3>
          <div class="continue-grid">
            <div
              v-for="item in inProgressPaths"
              :key="item.path_id"
              class="continue-card"
              @click="router.push(`/learning-paths/${item.path_id}`)"
            >
              <div class="continue-info">
                <span class="continue-name">{{ item.title }}</span>
                <span class="continue-stats">{{ item.completed_exercises }}/{{ item.total_exercises }} 题</span>
              </div>
              <el-progress
                :percentage="item.progress_percent"
                :stroke-width="8"
                :show-text="false"
                :color="item.progress_percent >= 80 ? '#67c23a' : '#8b5cf6'"
              />
              <span class="continue-pct">{{ item.progress_percent }}%</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 今日任务（已登录用户） -->
    <section class="section" v-if="userStore.isLoggedIn">
      <div class="container">
        <h2 class="section-title">
          <span class="title-text">🎯 今日任务</span>
          <span class="title-underline"></span>
        </h2>
        <div class="tasks-grid">
          <div
            v-for="task in dailyTasks"
            :key="task.id"
            class="task-card"
            :class="{ 'task-done': task.completed }"
          >
            <div class="task-icon">{{ task.icon }}</div>
            <div class="task-body">
              <div class="task-header-row">
                <span class="task-title">{{ task.title }}</span>
                <el-tag v-if="task.completed" type="success" size="small" effect="dark">已完成</el-tag>
              </div>
              <div class="task-desc">{{ task.description }}</div>
              <div class="task-progress-row">
                <el-progress
                  :percentage="Math.round(task.progress / task.target * 100)"
                  :stroke-width="6"
                  :show-text="false"
                  :color="task.completed ? '#67c23a' : '#8b5cf6'"
                />
                <span class="task-progress-text">{{ task.progress }}/{{ task.target }}</span>
              </div>
              <div class="task-reward">🎁 {{ task.reward }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 个性化推荐（已测评用户） -->
    <section class="section" v-if="userStore.isLoggedIn && userStore.assessmentCompleted && recommendedPaths.length > 0">
      <div class="container">
        <h2 class="section-title">
          <span class="title-text">为你推荐的学习路径</span>
          <span class="title-underline"></span>
        </h2>
        <p class="rec-subtitle">基于你的技能画像，我们为你精选了以下学习路线</p>
        <div class="rec-grid">
          <div
            v-for="rec in recommendedPaths"
            :key="rec.id"
            class="rec-card"
            @click="router.push(`/learning-paths/${rec.id}`)"
          >
            <div class="rec-badge">TOP {{ rec.priority }}</div>
            <h3 class="rec-title">{{ rec.title }}</h3>
            <p class="rec-desc">{{ rec.reason }}</p>
            <el-button type="primary" text class="rec-button">
              开始学习 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心优势 -->
    <section class="section">
      <div class="container">
        <h2 class="section-title">
          <span class="title-text">平台核心优势</span>
          <span class="title-underline"></span>
        </h2>
        <div class="advantage-grid">
          <div class="advantage-card">
            <span class="advantage-icon" style="color: var(--tm-color-primary)">📚</span>
            <h3 class="advantage-title">体系化课程</h3>
            <p class="advantage-desc">对标行业一线测试机构的课程体系，覆盖测试全领域</p>
          </div>
          <div class="advantage-card">
            <span class="advantage-icon" style="color: var(--tm-method-get)">✏️</span>
            <h3 class="advantage-title">实战习题</h3>
            <p class="advantage-desc">大量实战习题，边学边练，快速巩固知识点</p>
          </div>
          <div class="advantage-card">
            <span class="advantage-icon" style="color: #e6a23c">📈</span>
            <h3 class="advantage-title">进度跟踪</h3>
            <p class="advantage-desc">完整的学习进度跟踪系统，清晰掌握学习情况</p>
          </div>
          <div class="advantage-card">
            <span class="advantage-icon" style="color: #f56c6c">👤</span>
            <h3 class="advantage-title">职业规划</h3>
            <p class="advantage-desc">清晰的职业成长路径，从小白到测试架构师的完整路线</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()
const recommendedPaths = ref([])
const inProgressPaths = ref([])
const dailyTasks = ref([])
const dashboardData = ref({
  overallScore: null,
  overallLevel: '',
  exercisesDone: 0,
  interviewsDone: 0,
  achievementsUnlocked: 0,
})

onMounted(async () => {
  await nextTick()
  if (userStore.isLoggedIn) {
    fetchDashboardData()
  }
  if (userStore.isLoggedIn && userStore.assessmentCompleted) {
    try {
      const res = await request.get('/skills/radar')
      if (res.skills) {
        const weakSkills = res.skills
          .filter(s => s.score < 70)
          .sort((a, b) => a.score - b.score)
          .slice(0, 3)

        if (weakSkills.length > 0) {
          const pathRes = await request.get('/learning-paths')
          const allPaths = pathRes.items || pathRes || []
          const pathList = Array.isArray(allPaths) ? allPaths : []

          recommendedPaths.value = weakSkills.map((skill, idx) => {
            const matched = pathList.find(p =>
              (p.title || '').includes(skill.name.slice(0, 2)) ||
              (p.description || '').includes(skill.name.slice(0, 2))
            )
            return {
              id: matched ? matched.id : (pathList[idx % pathList.length]?.id || 1),
              priority: idx + 1,
              title: matched ? matched.title : `${skill.name}提升路线`,
              reason: `${skill.name}当前${skill.score}分（${skill.level}），${skill.suggestion}`,
            }
          })
        }
      }
    } catch (e) {
      console.error('获取推荐失败:', e)
    }
  }
})

const fetchDashboardData = async () => {
  if (!userStore.isLoggedIn) return
  try {
    const [skillsRes, achievementsRes, progressRes] = await Promise.allSettled([
      request.get('/skills/radar'),
      request.get('/achievements/'),
      request.get('/learning-paths/all-progress'),
    ])
    if (skillsRes.status === 'fulfilled' && skillsRes.value) {
      dashboardData.value.overallScore = skillsRes.value.overall_score
      dashboardData.value.overallLevel = skillsRes.value.overall_level
      const skills = skillsRes.value.skills || []
      dashboardData.value.exercisesDone = skills.filter(s => s.score > 0).length
    }
    if (achievementsRes.status === 'fulfilled' && achievementsRes.value) {
      dashboardData.value.achievementsUnlocked = achievementsRes.value.unlocked_count || 0
    }
    if (progressRes.status === 'fulfilled' && progressRes.value) {
      const allProgress = progressRes.value.progress || []
      const pathsRes = await request.get('/learning-paths')
      const pathList = Array.isArray(pathsRes) ? pathsRes : (pathsRes.items || [])
      const pathMap = {}
      for (const p of pathList) {
        pathMap[p.id] = p.title
      }
      inProgressPaths.value = allProgress
        .filter(p => p.completed_exercises > 0 && p.progress_percent < 100)
        .sort((a, b) => b.progress_percent - a.progress_percent)
        .slice(0, 4)
        .map(p => ({ ...p, title: pathMap[p.path_id] || `学习路径 #${p.path_id}` }))
    }
  } catch (e) {
    console.error('获取仪表盘数据失败:', e)
  }

  try {
    if (!userStore.isLoggedIn) return
    const tasksRes = await request.get('/exercise/daily-tasks')
    dailyTasks.value = tasksRes.tasks || []
  } catch {
    // silently fail
  }
}

const stages = [
  {
    id: 1,
    title: '测试入门筑基',
    desc: '建立测试思维，掌握基础理论和测试方法',
    duration: '4周',
    target: '测试实习生',
    color: '#ecf5ff',
    icon: '📚'
  },
  {
    id: 2,
    title: '功能测试精通',
    desc: '独立完成Web/APP/小程序等各类项目功能测试',
    duration: '8周',
    target: '初级测试工程师',
    color: '#f0f9ff',
    icon: '✏️'
  },
  {
    id: 3,
    title: '测试技术进阶',
    desc: '掌握接口测试、自动化测试基础、性能测试基础',
    duration: '12周',
    target: '中级测试工程师',
    color: '#fdf6ec',
    icon: '📈'
  },
  {
    id: 4,
    title: '自动化测试专家',
    desc: '搭建自动化测试框架，完成UI/接口/性能自动化',
    duration: '16周',
    target: '高级测试工程师',
    color: '#fef0f0',
    icon: '⚙️'
  },
  {
    id: 5,
    title: '测试架构师之路',
    desc: '测试平台开发、质量体系建设、测试效能提升',
    duration: '20周+',
    target: '测试架构师/专家',
    color: '#f5f0ff',
    icon: '🏢'
  }
]

const goToLearningPaths = () => {
  router.push('/learning-paths')
}

const goToExercises = () => {
  router.push('/exercises')
}

const goToModule = (module) => {
  if (module === 'api') {
    // 接口调试统一跳转到自动化测试页面
    router.push('/auto-test')
  } else {
    // 自动化测试在习题列表筛选
    router.push({
      path: '/exercises',
      query: { module: module }
    })
  }
}

const viewStagePaths = (stageId) => {
  router.push({
    path: '/learning-paths',
    query: { stage: stageId }
  })
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background-color: var(--tm-bg-page);
}

/* ========== Hero Section - Dark Premium ========== */
.hero {
  background: #121212;
  color: var(--tm-text-primary);
  padding: 140px 0 120px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -20%;
  width: 140%;
  height: 200%;
  background: radial-gradient(ellipse at 50% 50%, rgba(214, 51, 108, 0.08) 0%, transparent 60%);
  animation: heroGlow 8s ease-in-out infinite alternate;
}

@keyframes heroGlow {
  0% { opacity: 0.5; transform: scale(1); }
  100% { opacity: 1; transform: scale(1.1); }
}

.container {
  width: 100%;
  max-width: 1440px;
  padding: 0 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  margin-bottom: 24px;
  letter-spacing: -0.03em;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;

  span {
    display: block;
    font-size: 28px;
    font-weight: 400;
    -webkit-text-fill-color: var(--tm-text-secondary);
    margin-top: 12px;
    letter-spacing: 0.02em;
  }
}

.hero-subtitle {
  font-size: 20px;
  margin-bottom: 48px;
  color: var(--tm-text-secondary);
  font-weight: 300;
  line-height: 1.7;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.hero-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
}

.btn-primary {
  background: var(--tm-gradient-brand);
  border: none;
  color: #fff;
  font-weight: 600;
  padding: 16px 44px;
  font-size: 16px;
  border-radius: 12px;
  box-shadow: var(--tm-gradient-brand-glow);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: var(--tm-gradient-brand-hover);
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(214, 51, 108, 0.5);
  }
}

.btn-secondary {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border: var(--tm-glass-border);
  color: var(--tm-text-primary);
  font-weight: 500;
  padding: 14px 40px;
  font-size: 16px;
  border-radius: 12px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(214, 51, 108, 0.3);
    transform: translateY(-3px);
    box-shadow: var(--tm-shadow-glow);
  }
}

/* ========== Section ========== */
.section {
  padding: 96px 0;
}

.section-bg-light {
  background-color: rgba(255, 255, 255, 0.02);
}

.section-title {
  text-align: center;
  margin-bottom: 64px;
  position: relative;

  .title-text {
    display: inline-block;
    font-size: 36px;
    font-weight: 700;
    color: var(--tm-text-primary);
    padding: 0 24px;
    background-color: var(--tm-bg-page);
    position: relative;
    z-index: 1;
  }

  .title-underline {
    display: block;
    width: 80px;
    height: 3px;
    background: var(--tm-gradient-brand);
    margin: 16px auto 0;
    border-radius: 2px;
    box-shadow: 0 0 12px rgba(214, 51, 108, 0.4);
  }
}

/* ========== Stage Grid - Glassmorphism Cards ========== */
.stage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.stage-card {
  background: var(--tm-glass-bg) !important;
  backdrop-filter: var(--tm-glass-blur) !important;
  -webkit-backdrop-filter: var(--tm-glass-blur) !important;
  border: var(--tm-glass-border) !important;
  border-radius: 16px !important;
  box-shadow: var(--tm-shadow-card) !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;

  :deep(.el-card__body) {
    padding: 0;
  }

  &:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover) !important;
    border-color: rgba(214, 51, 108, 0.2) !important;
  }
}

.stage-inner {
  padding: 32px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.stage-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  background: rgba(214, 51, 108, 0.1);
  border: 1px solid rgba(214, 51, 108, 0.15);

  .icon-text {
    font-size: 28px;
  }
}

.stage-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--tm-text-primary);
}

.stage-desc {
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
  line-height: 1.7;
  flex: 1;
  font-size: 14px;
}

.stage-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 0;
  border-top: 1px solid var(--tm-border-light);
  border-bottom: 1px solid var(--tm-border-light);
}

.stage-target {
  font-size: 13px;
  color: var(--tm-text-secondary);
  font-weight: 400;
}

.stage-button {
  margin-top: auto;
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-color-primary);
}

/* ========== Advantage Grid - Minimal ========== */
.advantage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.advantage-card {
  text-align: center;
  padding: 36px 24px;
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 16px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
    border-color: rgba(214, 51, 108, 0.15);
  }
}

.advantage-icon {
  display: block;
  font-size: 40px;
  margin-bottom: 16px;
}

.advantage-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 10px;
  color: var(--tm-text-primary);
}

.advantage-desc {
  color: var(--tm-text-secondary);
  line-height: 1.7;
  font-size: 14px;
}

/* ========== Module Grid ========== */
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 32px;
}

.module-card {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 20px;
  padding: 48px 32px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  cursor: pointer;

  &:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
    border-color: rgba(214, 51, 108, 0.2);
  }
}

.module-icon {
  display: block;
  font-size: 56px;
  margin-bottom: 20px;
}

.module-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}

.module-desc {
  color: var(--tm-text-secondary);
  line-height: 1.7;
  margin-bottom: 24px;
  font-size: 15px;
}

.module-button {
  font-size: 15px;
  font-weight: 500;
  color: var(--tm-color-primary);
}

/* ========== Dashboard - Glass Cards ========== */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.dash-card {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 16px;
  padding: 28px 20px;
  text-align: center;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.dash-card:hover {
  transform: translateY(-6px) scale(1.03);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.dash-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.dash-value {
  font-size: 36px;
  font-weight: 900;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 8px;
  font-variant-numeric: tabular-nums;
}

.dash-label {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-bottom: 4px;
}

.dash-level {
  font-size: 12px;
  font-weight: 600;
  color: var(--tm-color-primary);
}

.dash-sub {
  font-size: 12px;
  color: var(--tm-color-primary);
  margin-top: 4px;
}

/* ========== Continue Learning - Gradient Progress ========== */
.continue-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid var(--tm-border-light);
}

.continue-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 20px;
}

.continue-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.continue-card {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 12px;
  padding: 20px;
  border: var(--tm-glass-border);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.continue-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.continue-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.continue-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.continue-stats {
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.continue-pct {
  display: block;
  text-align: right;
  font-size: 12px;
  color: var(--tm-color-primary);
  font-weight: 600;
  margin-top: 6px;
}

/* ========== Tasks ========== */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.task-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 14px;
  border: var(--tm-glass-border);
  transition: all 0.3s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tm-shadow-glow);
  border-color: rgba(214, 51, 108, 0.15);
}

.task-card.task-done {
  opacity: 0.6;
  border-color: rgba(81, 207, 102, 0.15);
}

.task-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.task-body {
  flex: 1;
  min-width: 0;
}

.task-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.task-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.task-desc {
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-bottom: 10px;
}

.task-progress-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.task-progress-row .el-progress {
  flex: 1;
}

.task-progress-text {
  font-size: 12px;
  color: var(--tm-text-secondary);
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
}

.task-reward {
  font-size: 12px;
  color: var(--tm-color-primary);
}

/* ========== Recommended ========== */
.rec-subtitle {
  text-align: center;
  color: var(--tm-text-secondary);
  font-size: 15px;
  margin-bottom: 40px;
  margin-top: -40px;
}

.rec-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.rec-card {
  background: var(--tm-glass-bg);
  backdrop-filter: var(--tm-glass-blur);
  -webkit-backdrop-filter: var(--tm-glass-blur);
  border-radius: 16px;
  padding: 32px 24px;
  border: var(--tm-glass-border);
  box-shadow: var(--tm-shadow-card);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.rec-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: var(--tm-shadow-glow), var(--tm-shadow-hover);
  border-color: rgba(214, 51, 108, 0.2);
}

.rec-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: var(--tm-gradient-brand);
  padding: 4px 10px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.rec-card .rec-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
  margin: 0 0 12px 0;
}

.rec-card .rec-desc {
  color: var(--tm-text-secondary);
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 20px;
}

.rec-button {
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-color-primary);
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .hero {
    padding: 80px 0 64px;
  }

  .hero-title {
    font-size: 40px;

    span {
      font-size: 20px;
    }
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .hero-buttons {
    flex-direction: column;
    gap: 16px;
  }

  .btn-primary,
  .btn-secondary {
    width: 80%;
  }

  .section {
    padding: 56px 0;
  }

  .section-title {
    .title-text {
      font-size: 28px;
    }
  }

  .section-title {
    margin-bottom: 48px;
  }
}
</style>
