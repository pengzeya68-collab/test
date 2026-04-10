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
            <h3 class="module-title">接口测试</h3>
            <p class="module-desc">RESTful API、Postman、JMeter、pytest 接口自动化练习</p>
            <el-button type="primary" text class="module-button">
              开始练习 <el-icon><ArrowRight /></el-icon>
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
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

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
    // 接口测试跳转到在线工具页面
    router.push('/interface-test')
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

/* ========== Hero Section ========== */
.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  padding: 120px 0;
  text-align: center;
  position: relative;
  overflow: hidden;
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
  font-size: 56px;
  font-weight: 800;
  margin-bottom: 24px;
  letter-spacing: -0.02em;

  span {
    display: block;
    font-size: 32px;
    font-weight: 400;
    opacity: 0.9;
    margin-top: 8px;
  }
}

.hero-subtitle {
  font-size: 22px;
  margin-bottom: 48px;
  opacity: 0.92;
  font-weight: 300;
  line-height: 1.6;
}

.hero-buttons {
  display: flex;
  gap: 24px;
  justify-content: center;
  align-items: center;
}

.btn-primary {
  background: #ffffff;
  border: none;
  color: #667eea;
  font-weight: 600;
  padding: 16px 40px;
  font-size: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;

  &:hover {
    background: #f8f8f8;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    color: #667eea;
  }
}

.btn-secondary {
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.8);
  color: #ffffff;
  font-weight: 500;
  padding: 14px 36px;
  font-size: 16px;
  border-radius: 8px;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #ffffff;
    color: #ffffff;
    transform: translateY(-2px);
  }
}

/* ========== Section ========== */
.section {
  padding: 96px 0;
}

.section-bg-light {
  background-color: var(--tm-bg-hover);
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
    width: 120px;
    height: 4px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    margin: 12px auto 0;
    border-radius: 2px;
  }
}

/* ========== Stage Grid ========== */
.stage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
}

.stage-card {
  border-radius: 12px;
  transition: all 0.3s ease;

  :deep(.el-card__body) {
    padding: 0;
  }

  &:hover {
    transform: translateY(-6px);
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
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;

  .icon-text {
    font-size: 36px;
  }
}

.stage-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--tm-text-primary);
}

.stage-desc {
  color: var(--tm-text-regular);
  margin-bottom: 20px;
  line-height: 1.7;
  flex: 1;
}

.stage-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 0;
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
  font-size: 15px;
  font-weight: 500;
}

/* ========== Advantage Grid ========== */
.advantage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 32px;
}

.advantage-card {
  text-align: center;
  padding: 32px 24px;
  background: var(--tm-bg-card);
  border-radius: 12px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
  }
}

.advantage-icon {
  display: block;
  font-size: 56px;
  margin-bottom: 16px;
}

.advantage-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--tm-text-primary);
}

.advantage-desc {
  color: var(--tm-text-regular);
  line-height: 1.7;
}

/* ========== Module Grid ========== */
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 40px;
}

.module-card {
  background: var(--tm-bg-card);
  border-radius: 16px;
  padding: 56px 32px;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  text-align: center;
  cursor: pointer;

  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.12);
  }
}

.module-icon {
  display: block;
  font-size: 72px;
  margin-bottom: 24px;
}

.module-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 16px;
  color: var(--tm-text-primary);
}

.module-desc {
  color: var(--tm-text-regular);
  line-height: 1.7;
  margin-bottom: 28px;
  font-size: 16px;
}

.module-button {
  font-size: 16px;
  font-weight: 500;
}

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .hero {
    padding: 64px 0;
  }

  .hero-title {
    font-size: 36px;

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
