<template>
  <div class="home-container">
    <div class="hero-banner">
      <h1 class="hero-title">TestMaster</h1>
      <p class="hero-subtitle">测试工程师成长平台</p>
      <p class="hero-desc">从小白到测试架构师的完整学习路径，一站式提升测试能力</p>
      <div class="hero-actions">
        <button class="btn-primary" @click="goToLearningPaths">开始学习</button>
        <button class="btn-secondary" @click="goToExercises">习题练习</button>
      </div>
      <div class="hero-search">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索习题、帖子、考试..."
          size="large"
          clearable
          @keyup.enter="doSearch"
          class="hero-search-input"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
          <template #append>
            <el-button @click="doSearch">搜索</el-button>
          </template>
        </el-input>
      </div>
    </div>

    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">5大学习阶段，循序渐进</h2>
        <div class="title-glow-line"></div>
      </div>
      <div class="grid-layout cols-3">
        <div class="standard-card stage-card" v-for="stage in stages" :key="stage.id" @click="viewStagePaths(stage.id)">
          <div class="card-icon">{{ stage.icon }}</div>
          <h3 class="card-title">{{ stage.title }}</h3>
          <p class="card-desc">{{ stage.desc }}</p>
          <div class="card-meta">
            <span class="badge">{{ stage.duration }}</span>
            <span class="role">{{ stage.target }}</span>
          </div>
          <button class="card-btn">探索学习路线 →</button>
        </div>
      </div>
    </section>

    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">专项练习专区</h2>
        <div class="title-glow-line"></div>
      </div>
      <div class="grid-layout cols-2">
        <div class="standard-card practice-card" @click="goToModule('automation')">
          <div class="card-icon">🤖</div>
          <h3 class="card-title">自动化测试</h3>
          <p class="card-desc">Selenium、Appium、Playwright、Cypress 自动化测试实战习题</p>
          <button class="btn-primary-sm">开始练习</button>
        </div>
        <div class="standard-card practice-card" @click="goToModule('api')">
          <div class="card-icon">🌐</div>
          <h3 class="card-title">接口调试 &amp; 自动化</h3>
          <p class="card-desc">在线接口调试、自动化测试场景编排、定时任务调度</p>
          <button class="btn-primary-sm">开始使用</button>
        </div>
      </div>
    </section>

    <div class="section-split-layout" v-if="userStore.isLoggedIn">
      <section class="split-left">
        <div class="section-header">
          <h2 class="section-title">我的学习仪表盘</h2>
          <div class="title-glow-line"></div>
        </div>
        <div class="grid-layout cols-2" style="gap: 16px;">
          <div class="mini-stat-card" @click="router.push('/skill-analysis')">
            <span class="stat-num">{{ dashboardData.overallScore || '--' }}</span>
            <span class="stat-label">综合得分<span class="stat-sub">({{ dashboardData.overallLevel || '未测评' }})</span></span>
          </div>
          <div class="mini-stat-card clickable" @click="router.push('/exercises')">
            <span class="stat-num">{{ dashboardData.exercisesDone }}</span>
            <span class="stat-label">完成习题 →</span>
          </div>
          <div class="mini-stat-card clickable" @click="router.push('/interview')">
            <span class="stat-num">{{ dashboardData.interviewsDone }}</span>
            <span class="stat-label">模拟面试 →</span>
          </div>
          <div class="mini-stat-card clickable" @click="router.push('/profile')">
            <span class="stat-num">{{ dashboardData.achievementsUnlocked }}</span>
            <span class="stat-label">成就勋章 →</span>
          </div>
          <div class="mini-stat-card clickable" @click="router.push('/favorites')">
            <span class="stat-num">{{ dashboardData.favoritesCount || 0 }}</span>
            <span class="stat-label">收藏夹 →</span>
          </div>
          <div class="mini-stat-card clickable" @click="router.push('/projects')">
            <span class="stat-num">{{ dashboardData.projectsCount || 0 }}</span>
            <span class="stat-label">项目实战 →</span>
          </div>
          <div class="mini-stat-card clickable" @click="router.push('/tools')">
            <span class="stat-num">🔧</span>
            <span class="stat-label">测试工具导航 →</span>
          </div>
        </div>

        <div v-if="inProgressPaths.length > 0" style="margin-top: 28px;">
          <div class="section-header">
            <h2 class="section-title">📖 继续学习</h2>
            <div class="title-glow-line"></div>
          </div>
          <div class="grid-layout cols-2" style="gap: 12px;">
            <div
              v-for="item in inProgressPaths"
              :key="item.path_id"
              class="progress-card"
              @click="router.push(`/learning-paths/${item.path_id}`)"
            >
              <div class="progress-card-info">
                <span class="progress-card-name">{{ item.title }}</span>
                <span class="progress-card-stats">{{ item.completed_exercises }}/{{ item.total_exercises }} 题</span>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" :style="{ width: item.progress_percent + '%' }"></div>
              </div>
              <span class="progress-pct">{{ item.progress_percent }}%</span>
            </div>
          </div>
        </div>
      </section>

      <section class="split-right">
        <div class="section-header">
          <h2 class="section-title">🎯 今日任务</h2>
          <div class="title-glow-line"></div>
        </div>
        <div class="task-list">
          <div
            v-for="task in dailyTasks"
            :key="task.id"
            class="task-item"
            :class="{ 'task-done': task.completed }"
          >
            <div class="task-info">
              <span class="task-name">{{ task.title }}</span>
              <el-tag v-if="task.completed" type="success" size="small" effect="dark">已完成</el-tag>
              <span class="task-progress-text">{{ task.progress }}/{{ task.target }}</span>
            </div>
            <p class="task-desc">{{ task.description }}</p>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: Math.round(task.progress / task.target * 100) + '%' }"></div>
            </div>
            <span class="task-reward">🎁 {{ task.reward }}</span>
          </div>
          <div v-if="dailyTasks.length === 0" class="task-empty">暂无任务</div>
        </div>
      </section>
    </div>

    <section class="dashboard-section" v-if="userStore.isLoggedIn && userStore.assessmentCompleted && recommendedPaths.length > 0">
      <div class="section-header">
        <h2 class="section-title">为你推荐的学习路径 <span class="sub-text">基于你的技能画像，为你精准精选了以下学习路线</span></h2>
        <div class="title-glow-line"></div>
      </div>
      <div class="grid-layout cols-3">
        <div
          class="standard-card path-card"
          v-for="rec in recommendedPaths"
          :key="rec.id"
          @click="router.push(`/learning-paths/${rec.id}`)"
        >
          <span class="top-tag">TOP {{ rec.priority }}</span>
          <h3 class="card-title">{{ rec.title }}</h3>
          <p class="card-desc">{{ rec.reason }}</p>
          <button class="btn-primary-sm">开始学习 →</button>
        </div>
      </div>
    </section>

    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">平台核心优势</h2>
        <div class="title-glow-line"></div>
      </div>
      <div class="grid-layout cols-4">
        <div class="advantage-card">
          <div class="adv-icon">📚</div>
          <h4 class="adv-title">体系化课程</h4>
          <p class="adv-desc">对标行业一线测试机构的课程体系，覆盖测试全领域</p>
        </div>
        <div class="advantage-card">
          <div class="adv-icon">✏️</div>
          <h4 class="adv-title">实战习题</h4>
          <p class="adv-desc">大量实战习题，边学边练，快速巩固知识点</p>
        </div>
        <div class="advantage-card">
          <div class="adv-icon">📈</div>
          <h4 class="adv-title">进度跟踪</h4>
          <p class="adv-desc">完整的学习进度跟踪系统，清晰掌握学习情况</p>
        </div>
        <div class="advantage-card">
          <div class="adv-icon">👤</div>
          <h4 class="adv-title">职业规划</h4>
          <p class="adv-desc">清晰的职业成长路径，从小白到测试架构师的完整路线</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()
const searchKeyword = ref('')
const doSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/search', query: { q: searchKeyword.value } })
  }
}
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
      if (e?.response?.status !== 401) {
        console.error('获取推荐失败:', e)
      }
    }
  }
})

const fetchDashboardData = async () => {
  if (!userStore.isLoggedIn) return
  try {
    const [skillsRes, achievementsRes, progressRes] = await Promise.allSettled([
      request.get('/skills/radar'),
      request.get('/achievements'),
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
    if (e?.response?.status !== 401) {
      console.error('获取仪表盘数据失败:', e)
    }
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
  { id: 1, title: '测试入门筑基', desc: '建立测试思维，掌握基础理论和测试方法', duration: '4周', target: '测试实习生', icon: '📚' },
  { id: 2, title: '功能测试精通', desc: '独立完成Web/APP/小程序等各类项目功能测试', duration: '8周', target: '初级测试工程师', icon: '✏️' },
  { id: 3, title: '测试技术进阶', desc: '掌握接口测试、自动化测试基础、性能测试基础', duration: '12周', target: '中级测试工程师', icon: '📈' },
  { id: 4, title: '自动化测试专家', desc: '搭建自动化测试框架，完成UI/接口/性能自动化', duration: '16周', target: '高级测试工程师', icon: '⚙️' },
  { id: 5, title: '测试架构师之路', desc: '测试平台开发、质量体系建设、测试效能提升', duration: '20周+', target: '测试架构师/专家', icon: '🏢' },
]

const goToLearningPaths = () => router.push('/learning-paths')
const goToExercises = () => router.push('/exercises')
const goToModule = (mod) => {
  if (mod === 'api') {
    router.push('/auto-test')
  } else {
    router.push({ path: '/exercises', query: { module: mod } })
  }
}
const viewStagePaths = (stageId) => router.push({ path: '/learning-paths', query: { stage: stageId } })
</script>

<style scoped>
/* ==================== 全局深度黑布局系统 ==================== */
.home-container {
  width: 100%;
  min-height: 100vh;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
  padding: 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

/* ==================== 统一标准的上下结构 Section ==================== */
.dashboard-section {
  width: 100%;
  display: block;
}

.section-header {
  width: 100%;
  margin-bottom: 24px;
  text-align: left;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0;
}
.section-title .sub-text {
  font-size: 13px;
  font-weight: 400;
  color: var(--tm-text-secondary);
  margin-left: 12px;
}

.title-glow-line {
  width: 48px;
  height: 3px;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px;
  margin-top: 10px;
}

/* ==================== Grid 系统 ==================== */
.grid-layout {
  display: grid;
  width: 100%;
  gap: 24px;
}
.grid-layout.cols-2 {
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
}
.grid-layout.cols-3 {
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}
.grid-layout.cols-4 {
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}

/* ==================== Hero Banner ==================== */
.hero-banner {
  width: 100%;
  padding: 48px 48px 42px;
  text-align: center;
  background: linear-gradient(135deg, var(--tm-bg-page) 0%, var(--tm-card-bg) 40%, rgba(var(--tm-color-primary-rgb), 0.06) 70%, var(--tm-bg-page) 100%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}
.hero-banner::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -30%;
  width: 160%;
  height: 200%;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(var(--tm-color-primary-rgb), 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(99, 102, 241, 0.10) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(0, 242, 254, 0.06) 0%, transparent 60%);
  animation: heroGlow 10s ease-in-out infinite alternate;
}
@keyframes heroGlow {
  0% { opacity: 0.6; transform: scale(1); }
  100% { opacity: 1; transform: scale(1.08); }
}

.hero-title {
  font-size: 42px;
  font-weight: 900;
  margin: 0 0 6px;
  letter-spacing: -0.03em;
  line-height: 1.2;
  background: linear-gradient(135deg, var(--tm-color-primary) 0%, var(--tm-color-primary) 15%, rgba(var(--tm-color-primary-rgb), 0.6) 50%, rgba(var(--tm-color-primary-rgb), 0.3) 85%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 20px rgba(var(--tm-color-primary-rgb), 0.3));
  position: relative;
  z-index: 1;
}

.hero-subtitle {
  font-size: 17px;
  font-weight: 400;
  color: var(--tm-text-regular);
  margin: 0 0 8px;
  position: relative;
  z-index: 1;
}

.hero-desc {
  font-size: 15px;
  color: var(--tm-text-secondary);
  margin: 0 0 24px;
  max-width: 460px;
  margin-left: auto;
  margin-right: auto;
  position: relative;
  z-index: 1;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  position: relative;
  z-index: 1;
}

/* ==================== 按钮 ==================== */
.btn-primary {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  color: #fff;
  font-weight: 600;
  padding: 13px 38px;
  font-size: 15px;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(var(--tm-color-primary-rgb), 0.35);
  transition: all 0.3s ease;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(var(--tm-color-primary-rgb), 0.5);
}

.btn-secondary {
  background: var(--tm-border-light);
  border: 1px solid var(--border-subtle);
  color: var(--tm-text-regular);
  font-weight: 500;
  padding: 13px 34px;
  font-size: 15px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.btn-secondary:hover {
  background: var(--border-subtle);
  border-color: rgba(var(--tm-color-primary-rgb), 0.3);
  transform: translateY(-2px);
}

.btn-primary-sm {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border: none;
  color: #fff;
  font-weight: 600;
  padding: 10px 24px;
  font-size: 14px;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(var(--tm-color-primary-rgb), 0.3);
  transition: all 0.3s ease;
}
.btn-primary-sm:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(var(--tm-color-primary-rgb), 0.4);
}

/* ==================== 标准卡片 ==================== */
.standard-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
  padding: 24px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}
.standard-card:hover {
  transform: translateY(-4px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.25);
  box-shadow: 0 8px 30px rgba(var(--tm-color-primary-rgb), 0.12);
}

.stage-card {
  cursor: pointer;
}
.stage-card .card-icon {
  font-size: 28px;
  margin-bottom: 14px;
}
.stage-card .card-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 6px;
}
.stage-card .card-desc {
  font-size: 13px;
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0 0 14px;
  flex: 1;
}
.stage-card .card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-top: 1px solid var(--tm-border-light);
  border-bottom: 1px solid var(--tm-border-light);
  margin-bottom: 14px;
}
.stage-card .badge {
  font-size: 12px;
  color: var(--tm-text-regular);
  background: rgba(var(--tm-color-primary-rgb), 0.12);
  padding: 2px 10px;
  border-radius: 6px;
}
.stage-card .role {
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.stage-card .card-btn {
  margin-top: auto;
  background: none;
  border: none;
  color: var(--tm-color-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  align-self: flex-start;
  transition: color 0.3s;
}
.stage-card .card-btn:hover {
  color: var(--tm-color-primary);
}

/* ==================== 专项练习卡片 ==================== */
.practice-card {
  text-align: center;
  cursor: pointer;
}
.practice-card .card-icon {
  font-size: 44px;
  margin-bottom: 14px;
}
.practice-card .card-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 8px;
}
.practice-card .card-desc {
  font-size: 14px;
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0 0 18px;
}
.practice-card .btn-primary-sm {
  align-self: center;
}

/* ==================== 左右分栏 ==================== */
.section-split-layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 28px;
  width: 100%;
}

.split-left,
.split-right {
  min-width: 0;
}

/* ==================== 仪表盘迷你统计卡 ==================== */
.mini-stat-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 12px;
  padding: 22px 16px;
  text-align: center;
  transition: all 0.3s ease;
}
.mini-stat-card.clickable {
  cursor: pointer;
}
.mini-stat-card.clickable:hover {
  transform: translateY(-3px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.25);
  box-shadow: 0 6px 24px rgba(var(--tm-color-primary-rgb), 0.1);
}
.stat-num {
  display: block;
  font-size: 30px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 6px;
}
.stat-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.stat-sub {
  color: var(--tm-color-primary);
  font-size: 11px;
  font-weight: 600;
}

/* ==================== 继续学习进度卡 ==================== */
.progress-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.progress-card:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.08);
}
.progress-card-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.progress-card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}
.progress-card-stats {
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.progress-pct {
  display: block;
  text-align: right;
  font-size: 11px;
  color: var(--tm-color-primary);
  font-weight: 600;
  margin-top: 4px;
}

/* ==================== 进度条通用 ==================== */
.progress-bar-bg {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-radius: 3px;
  transition: width 0.6s ease;
}

/* ==================== 任务列表 ==================== */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.task-item {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
}
.task-item:hover {
  border-color: rgba(var(--tm-color-primary-rgb), 0.15);
  box-shadow: 0 4px 16px rgba(var(--tm-color-primary-rgb), 0.08);
}
.task-item.task-done {
  opacity: 0.5;
}
.task-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.task-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text-primary);
}
.task-progress-text {
  font-size: 12px;
  color: var(--tm-text-secondary);
}
.task-desc {
  font-size: 12px;
  color: var(--tm-text-secondary);
  margin: 0 0 8px;
}
.task-item .progress-bar-bg {
  margin-bottom: 6px;
}
.task-reward {
  font-size: 11px;
  color: var(--tm-color-primary);
}
.task-empty {
  text-align: center;
  padding: 40px 0;
  color: var(--tm-text-secondary);
  font-size: 14px;
}

/* ==================== 推荐路径卡片 ==================== */
.path-card {
  cursor: pointer;
}
.top-tag {
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  padding: 3px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  align-self: flex-start;
}
.path-card .card-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 8px;
}
.path-card .card-desc {
  font-size: 13px;
  color: var(--tm-text-regular);
  line-height: 1.6;
  margin: 0 0 14px;
  flex: 1;
}
.path-card .btn-primary-sm {
  align-self: flex-start;
}

/* ==================== 优势卡片 ==================== */
.advantage-card {
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: 14px;
  padding: 28px 20px;
  text-align: center;
  transition: all 0.3s ease;
}
.advantage-card:hover {
  transform: translateY(-4px);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
  box-shadow: 0 6px 24px rgba(var(--tm-color-primary-rgb), 0.08);
}
.adv-icon {
  font-size: 34px;
  margin-bottom: 10px;
}
.adv-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text-primary);
  margin: 0 0 6px;
}
.adv-desc {
  font-size: 13px;
  color: var(--tm-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* ==================== Responsive ==================== */
@media (max-width: 900px) {
  .home-container { padding: 24px; gap: 36px; }
  .hero-banner { padding: 36px 24px 32px; }
  .section-split-layout { grid-template-columns: 1fr; }
  .grid-layout.cols-4 { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
}
@media (max-width: 600px) {
  .home-container { padding: 16px; gap: 28px; }
  .hero-banner { padding: 28px 16px 24px; }
  .hero-title { font-size: 30px; }
  .grid-layout.cols-2,
  .grid-layout.cols-3 { grid-template-columns: 1fr; }
}
</style>