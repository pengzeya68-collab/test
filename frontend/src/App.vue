<template>
  <div id="app" :class="{ 'has-sidebar': isLoggedIn && !isAuthPage }">
    <!-- 顶部导航栏 -->
    <el-header class="navbar" v-if="!isAuthPage">
      <div class="container">
        <div class="nav-left">
          <router-link to="/" class="logo">
            <span class="logo-text">TestMaster</span>
          </router-link>
          <div class="nav-menu" v-if="!isLoggedIn">
            <router-link to="/" class="nav-item" :class="{ 'is-active': activeMenu === '/' }">首页</router-link>
            <router-link to="/learning-paths" class="nav-item">学习路径</router-link>
            <router-link to="/exercises" class="nav-item">习题库</router-link>
            <router-link to="/community" class="nav-item">社区</router-link>
          </div>
        </div>
        <div class="nav-right">
          <el-dropdown trigger="click" @command="changeTheme" v-if="!isAuthPage">
            <el-button link class="theme-btn">
              <el-icon><Brush /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="theme in themes" :key="theme.id" :command="theme.id">
                  <span class="theme-color-dot" :style="{ backgroundColor: theme.primary }"></span>
                  {{ theme.name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <template v-if="isLoggedIn">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="9" class="checkin-badge">
              <el-button link class="theme-btn" @click="showCheckinDialog = true">
                <el-icon><Calendar /></el-icon>
                <span>签到</span>
              </el-button>
            </el-badge>
            <el-dropdown @command="handleMenuCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                <span class="username">{{ userInfo?.username }}</span>
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" @click="goToLogin">登录</el-button>
            <el-button @click="goToRegister" style="margin-left: 10px;">注册</el-button>
          </template>
        </div>
      </div>
    </el-header>

    <!-- 侧边栏 + 主内容 -->
    <div class="layout-body" v-if="isLoggedIn && !isAuthPage">
      <aside class="sidebar">
        <div class="sidebar-scroll">
          <div class="sidebar-group" v-for="group in sidebarGroups" :key="group.label">
            <div class="sidebar-label">{{ group.label }}</div>
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="sidebar-item"
              :class="{ active: isSidebarActive(item.path) }"
            >
              <span class="sidebar-icon">{{ item.icon }}</span>
              <span class="sidebar-text">{{ item.name }}</span>
              <el-badge v-if="item.badge" :value="item.badge" :max="9" class="sidebar-badge" />
            </router-link>
          </div>
        </div>
      </aside>
      <main class="main-content-with-sidebar">
        <router-view :key="$route.fullPath" />
      </main>
    </div>

    <!-- 未登录主内容 -->
    <main class="main-content" v-if="!isLoggedIn || isAuthPage">
      <router-view :key="$route.fullPath" />
    </main>

    <!-- 页脚 -->
    <footer class="footer" v-if="!isAuthPage && !isLoggedIn">
      <div class="container">
        <p>© 2026 TestMaster 测试工程师成长平台</p>
      </div>
    </footer>

    <!-- 签到弹窗 -->
    <el-dialog
      v-model="showCheckinDialog"
      title="每日签到"
      width="420px"
      :close-on-click-modal="true"
      class="checkin-dialog"
    >
      <div class="checkin-content">
        <div class="checkin-streak" v-if="checkinStatus.current_streak > 0">
          <div class="streak-number">{{ checkinStatus.current_streak }}</div>
          <div class="streak-label">天连续签到</div>
        </div>
        <div class="checkin-streak" v-else>
          <div class="streak-number">0</div>
          <div class="streak-label">尚未签到</div>
        </div>

        <div class="checkin-calendar">
          <div
            v-for="day in checkinStatus.last_7_days"
            :key="day.date"
            class="calendar-day"
            :class="{ checked: day.checked }"
          >
            <div class="day-dot">{{ day.checked ? '✓' : '·' }}</div>
            <div class="day-label">{{ day.date.slice(5) }}</div>
          </div>
        </div>

        <div class="checkin-reward">
          <span>明日签到可获得 <strong>{{ checkinStatus.next_reward || 5 }}</strong> 经验</span>
        </div>

        <el-button
          v-if="!checkinStatus.checked_in_today"
          type="primary"
          size="large"
          class="checkin-btn"
          @click="doCheckin"
          :loading="checkinLoading"
        >
          立即签到
        </el-button>
        <el-button
          v-else
          type="success"
          size="large"
          class="checkin-btn"
          disabled
        >
          今日已签到 ✓
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, ArrowDown, Brush, Calendar } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { themes, loadSavedTheme, applyTheme } from '@/utils/ThemeConfig'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)
const userInfo = computed(() => userStore.userInfo)

const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register' || route.path.startsWith('/admin') || route.path === '/assessment'
})

const activeMenu = computed(() => route.path)

const sidebarGroups = computed(() => {
  const groups = [
    {
      label: '学习',
      items: [
        { name: '首页', path: '/', icon: '🏠' },
        { name: '学习路径', path: '/learning-paths', icon: '🗺️' },
        { name: '习题库', path: '/exercises', icon: '✏️' },
        { name: '错题本', path: '/wrong-answers', icon: '📖' },
        { name: '模考大赛', path: '/exams', icon: '📝' },
      ],
    },
    {
      label: '面试',
      items: [
        { name: '面试模拟', path: '/interview', icon: '🎤' },
        { name: '面试题库', path: '/interview', icon: '📋' },
        { name: '我的面试', path: '/interview/my', icon: '📁' },
      ],
    },
    {
      label: '工具',
      items: [
        { name: 'AI导师', path: '/ai-tutor', icon: '🤖' },
        { name: '代码练习室', path: '/code-playground', icon: '💻' },
        { name: '自动化测试', path: '/auto-test', icon: '⚙️' },
      ],
    },
    {
      label: '成长',
      items: [
        { name: '技能分析', path: '/skill-analysis', icon: '📊' },
        { name: '排行榜', path: '/leaderboard', icon: '🏆' },
        { name: '学习周报', path: '/weekly-report', icon: '📈' },
        { name: '技能证书', path: '/certificates', icon: '🎓' },
      ],
    },
    {
      label: '社区',
      items: [
        { name: '社区交流', path: '/community', icon: '💬' },
      ],
    },
  ]

  if (!userStore.assessmentCompleted) {
    groups[0].items.push({ name: '入学测评', path: '/assessment', icon: '🎯' })
  }

  if (!checkinStatus.value.checked_in_today) {
    const learnGroup = groups[0]
    const homeItem = learnGroup.items.find(i => i.path === '/')
    if (homeItem) {
      homeItem.badge = '!'
    }
  }

  return groups
})

const isSidebarActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const showCheckinDialog = ref(false)
const checkinLoading = ref(false)
const unreadCount = ref(0)
const checkinStatus = ref({
  checked_in_today: false,
  current_streak: 0,
  total_checkins: 0,
  next_reward: 5,
  last_7_days: [],
})

onMounted(() => {
  const savedThemeId = loadSavedTheme()
  applyTheme(savedThemeId)
  if (userStore.isLoggedIn) {
    fetchCheckinStatus()
  }
})

watch(
  () => route.path,
  () => {
    if (userStore.isLoggedIn && !userStore.assessmentCompleted) {
      userStore.checkAssessmentStatus()
    }
  }
)

const fetchCheckinStatus = async () => {
  try {
    const res = await request.get('/checkin/status')
    checkinStatus.value = res
    unreadCount.value = res.checked_in_today ? 0 : 1
  } catch {
    // silently fail
  }
}

const doCheckin = async () => {
  checkinLoading.value = true
  try {
    const res = await request.post('/checkin/')
    if (res.checked_in) {
      ElNotification({
        title: '🎉 签到成功！',
        message: `连续${res.streak}天签到，获得 ${res.exp_earned} 经验！`,
        type: 'success',
        duration: 4000,
        position: 'top-right',
      })
      checkinStatus.value.checked_in_today = true
      checkinStatus.value.current_streak = res.streak
      unreadCount.value = 0
      await fetchCheckinStatus()
      userStore.checkNewAchievements()
    } else {
      ElMessage.info(res.message)
    }
  } catch (error) {
    ElMessage.error('签到失败，请稍后重试')
  } finally {
    checkinLoading.value = false
  }
}

const changeTheme = (themeId) => {
  const theme = applyTheme(themeId)
  ElMessage.success(`已切换至「${theme.name}」主题`)
}

const handleMenuCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleLogout = () => {
  ElMessageBox.confirm(
    '确定要退出登录吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    userStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  }).catch(() => {})
}

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

const handleMenuSelect = (index) => {
  router.push(index)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 后台页面高度适配 */
.admin-page {
  height: 100vh;
  overflow: hidden;
}

.container {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 0 40px;
  box-sizing: border-box;
}

/* 导航栏 */
.navbar {
  background: rgba(18, 18, 18, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06);
  height: 64px;
  line-height: 64px;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.navbar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 48px;
}

.logo {
  text-decoration: none;
}

.logo-text {
  font-size: 22px;
  font-weight: bold;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  display: flex;
  gap: 8px;
  height: 64px;
  align-items: center;
}

.nav-item {
  text-decoration: none;
  color: var(--tm-text-regular);
  height: 64px;
  line-height: 64px;
  padding: 0 16px;
  border-bottom: 2px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--tm-radius-small) var(--tm-radius-small) 0 0;
}

.nav-item:hover {
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.04);
}

.nav-item.is-active {
  border-bottom-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
  font-weight: 600;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.layout-body {
  display: flex;
  flex: 1;
  min-height: calc(100vh - 64px);
}

.sidebar {
  width: 220px;
  background: rgba(18, 18, 18, 0.9);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 64px;
  height: calc(100vh - 64px);
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-scroll {
  padding: 16px 0;
}

.sidebar-group {
  margin-bottom: 8px;
}

.sidebar-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--tm-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 20px 4px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 20px;
  text-decoration: none;
  color: var(--tm-text-regular);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.sidebar-item:hover {
  background: rgba(214, 51, 108, 0.06);
  color: var(--tm-color-primary);
}

.sidebar-item.active {
  background: rgba(214, 51, 108, 0.1);
  color: var(--tm-color-primary);
  border-left-color: var(--tm-color-primary);
  font-weight: 600;
}

.sidebar-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.sidebar-text {
  flex: 1;
}

.sidebar-badge {
  flex-shrink: 0;
}

.main-content-with-sidebar {
  flex: 1;
  min-width: 0;
  overflow-x: hidden;
}

.checkin-badge {
  line-height: 1;
}

.checkin-content {
  text-align: center;
  padding: 10px 0;
}

.checkin-streak {
  margin-bottom: 24px;
}

.streak-number {
  font-size: 64px;
  font-weight: 900;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.streak-label {
  font-size: 16px;
  color: var(--tm-text-secondary);
  margin-top: 8px;
}

.checkin-calendar {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.calendar-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.day-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.06);
  color: var(--tm-text-secondary);
  transition: all 0.3s;
}

.calendar-day.checked .day-dot {
  background: var(--tm-gradient-brand);
  color: white;
}

.day-label {
  font-size: 12px;
  color: var(--tm-text-secondary);
}

.checkin-reward {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
}

.checkin-reward strong {
  color: var(--tm-color-primary);
  font-size: 18px;
}

.checkin-btn {
  width: 200px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 24px;
  height: 44px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--tm-text-regular);
  padding: 8px 12px;
  border-radius: var(--tm-radius-small);
  transition: all 0.2s;
}

.user-info:hover {
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.08);
}

.username {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

/* 主内容 */
.main-content {
  flex: 1;
  background: var(--tm-bg-page);
}

/* 页脚 */
.footer {
  background: rgba(18, 18, 18, 0.9);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 24px 0;
  text-align: center;
  color: var(--tm-text-secondary);
  font-size: 13px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 40px;
}

/* 响应式 */
@media (max-width: 768px) {
  .nav-left {
    gap: 20px;
  }

  .logo-text {
    font-size: 18px;
  }

  .nav-menu {
    display: none;
  }

  .username {
    display: none;
  }
}

/* 主题切换按钮 */
.theme-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--tm-color-primary);
  font-size: 14px;
  padding: 6px 12px;
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.3);
  border-radius: 6px;
  transition: all 0.2s;
}

.theme-btn:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  color: var(--tm-color-primary);
}

.theme-color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* 混合响应式布局 - 两种核心容器样式 */

/* 1. 满屏工作区布局（适用于表格、代码IDE、工具类页面） */
.layout-fluid {
  width: 100%;
  max-width: 100%;
  padding: 20px 32px;
  margin: 0 auto;
  box-sizing: border-box;
}

/* 2. 聚焦阅读布局（适用于首页、卡片、问答社区、题库 - 最佳阅读宽度） */
.layout-constrained {
  width: 100%;
  max-width: 1440px;
  padding: 20px 24px;
  margin: 0 auto;
  box-sizing: border-box;
}

/* 通用卡片网格布局 */
.grid-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}
</style>
