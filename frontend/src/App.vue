<template>
  <el-config-provider :locale="zhCn">
    <div id="app" :class="{ 'has-sidebar': isLoggedIn && !isAuthPage }">
    <!-- 顶部导航栏 -->
    <header class="navbar" v-if="!isAuthPage">
      <div class="container">
        <div class="nav-left">
          <router-link to="/" class="logo">
            <span class="logo-text">TestMaster</span>
          </router-link>
          <el-icon class="nav-burger" @click="navOpen = !navOpen"><Menu /></el-icon>
          <div class="nav-menu" :class="{ open: navOpen }" v-if="!isLoggedIn">
            <router-link to="/" class="nav-item" :class="{ 'is-active': activeMenu === '/' }" @click="navOpen = false">首页</router-link>
            <router-link to="/learning-paths" class="nav-item" @click="navOpen = false">学习路径</router-link>
            <router-link to="/exercises" class="nav-item" @click="navOpen = false">习题库</router-link>
            <router-link to="/tools" class="nav-item" @click="navOpen = false">工具导航</router-link>
            <router-link to="/community" class="nav-item" @click="navOpen = false">社区</router-link>
          </div>
        </div>
        <div class="nav-right">
          <span v-if="isDesktopBuild" :class="['desktop-engine', { ready: desktopReady }]"><i></i>{{ desktopReady ? '桌面执行引擎正常' : '桌面执行引擎未连接' }}</span>
          <el-dropdown trigger="click" @command="changeTheme" v-if="!isAuthPage">
            <el-button link class="theme-btn">
              <el-icon><Brush /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="theme in themes" :key="theme.id" :command="theme.id">
                  <span class="theme-color-dot" :style="{ backgroundColor: theme.primary }"></span>
                  {{ themeDisplayName(theme) }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <template v-if="isLoggedIn">
            <NotificationBell />
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
                  <el-dropdown-item command="favorites">我的收藏</el-dropdown-item>
                  <el-dropdown-item command="notifications">通知消息</el-dropdown-item>
                  <el-dropdown-item command="tools">测试工具</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
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
    </header>

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
              :title="item.name"
            >
              <span class="sidebar-icon"><el-icon><component :is="item.icon" /></el-icon></span>
              <span class="sidebar-text">{{ item.name }}</span>
              <el-badge v-if="item.badge" :value="item.badge" :max="9" class="sidebar-badge" />
            </router-link>
          </div>
        </div>
      </aside>
      <main class="main-content-with-sidebar">
        <router-view v-slot="{ Component }">
          <transition name="tm-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 未登录主内容 -->
    <main class="main-content" v-if="!isLoggedIn || isAuthPage">
      <router-view v-slot="{ Component }">
        <transition name="tm-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
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
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, ArrowDown, Brush, Calendar, Menu, House, MapLocation, EditPen, Notebook, Tickets, Microphone, List, Folder, ChatDotRound, Monitor, Setting, Lightning, DocumentCopy, DataLine, Guide, TrendCharts, Trophy, Calendar as CalendarIcon, Medal, ChatLineRound, Aim } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { themes, loadSavedTheme, applyTheme } from '@/utils/ThemeConfig'
import { useUserStore } from '@/stores/user'
import NotificationBell from '@/components/NotificationBell.vue'
import request from '@/utils/request'
import { isDesktopBuild } from '@/utils/build-target'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const desktopReady = computed(() => typeof window !== 'undefined' && typeof window.testmaster?.execution?.runCase === 'function')

// 移动端汉堡菜单状态
const navOpen = ref(false)
const closeNavOnResize = () => {
  if (window.innerWidth > 768) navOpen.value = false
}

const isLoggedIn = computed(() => userStore.isLoggedIn)
const userInfo = computed(() => userStore.userInfo)

const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register' || route.path.startsWith('/admin')
})

const activeMenu = computed(() => route.path)

const sidebarGroups = computed(() => {
  if (isDesktopBuild) return [
    { label: '工作台', items: [
      { name: '自动化总览', path: '/auto-test', icon: House },
      { name: '接口自动化', path: '/auto-test', icon: Setting },
      { name: 'UI 自动化用例', path: '/ui-automation/cases', icon: Monitor },
      { name: 'UI 回归套件', path: '/ui-automation/suites', icon: Tickets },
    ]},
    { label: '接口资产', items: [
      { name: '接口用例', path: '/cases', icon: DocumentCopy },
      { name: '业务场景', path: '/scenarios', icon: Guide },
      { name: '接口回归套件', path: '/suites', icon: Folder },
      { name: '测试数据工厂', path: '/data-factory', icon: DataLine },
      { name: 'Mock 服务', path: '/mock-service', icon: Lightning },
    ]},
    { label: '质量工具', items: [
      { name: 'JMeter 性能助手', path: '/jmeter-assistant', icon: Lightning },
      { name: 'AI 生成用例', path: '/ai-generate-cases', icon: DocumentCopy },
      { name: '测试覆盖率', path: '/test-coverage', icon: TrendCharts },
      { name: 'API 文档', path: '/api-docs', icon: Notebook },
      { name: '自动化资产备份', path: '/backup-manager', icon: Folder },
      { name: '测试工具导航', path: '/tools', icon: Guide },
    ]},
  ]
  const groups = [
    {
      label: '学习',
      items: [
        { name: '首页', path: '/', icon: House },
        { name: '学习路径', path: '/learning-paths', icon: MapLocation },
        { name: '习题库', path: '/exercises', icon: EditPen },
        { name: '错题本', path: '/wrong-answers', icon: Notebook },
        { name: '模考大赛', path: '/exams', icon: Tickets },
      ],
    },
    {
      label: '面试',
      items: [
        { name: '面试模拟', path: '/interview/simulate', icon: Microphone },
        { name: '面试题库', path: '/interview', icon: List },
        { name: '我的面试', path: '/interview/my', icon: Folder },
      ],
    },
    {
      label: '工具',
      items: [
        { name: 'AI导师', path: '/ai-tutor', icon: ChatDotRound },
        { name: '代码练习室', path: '/code-playground', icon: Monitor },
        { name: '自动化测试', path: '/auto-test', icon: Setting },
        { name: 'JMeter 助手', path: '/jmeter-assistant', icon: Lightning },
        { name: 'AI生成用例', path: '/ai-generate-cases', icon: DocumentCopy },
        { name: '覆盖率看板', path: '/test-coverage', icon: DataLine },
        { name: '测试工具导航', path: '/tools', icon: Guide },
      ],
    },
    {
      label: '成长',
      items: [
        { name: '技能分析', path: '/skill-analysis', icon: TrendCharts },
        { name: '排行榜', path: '/leaderboard', icon: Trophy },
        { name: '学习周报', path: '/weekly-report', icon: CalendarIcon },
        { name: '技能证书', path: '/certificates', icon: Medal },
      ],
    },
    {
      label: '社区',
      items: [
        { name: '社区交流', path: '/community', icon: ChatLineRound },
      ],
    },
  ]

  if (!userStore.assessmentCompleted) {
    groups[0].items.push({ name: '入学测评', path: '/assessment', icon: Aim })
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

onMounted(async () => {
  const savedThemeId = isDesktopBuild && !localStorage.getItem('testmaster-theme') ? 'apple-light' : loadSavedTheme()
  applyTheme(savedThemeId)
  window.addEventListener('resize', closeNavOnResize)
  if (userStore.isLoggedIn && !isAuthPage.value) {
    fetchCheckinStatus()
    // 启动时同步测评状态，避免 localStorage 缓存过期
    try {
      await userStore.checkAssessmentStatus()
    } catch {
      // 路由守卫会处理失败情况
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', closeNavOnResize)
})


const fetchCheckinStatus = async () => {
  try {
    const res = await request.get('/checkin/status')
    checkinStatus.value = res
    unreadCount.value = res.checked_in_today ? 0 : 1
  } catch {
    // 获取签到状态失败时，假设已签到以避免误显示提示
    checkinStatus.value = { ...checkinStatus.value, checked_in_today: true }
    unreadCount.value = 0
  }
}

const doCheckin = async () => {
  checkinLoading.value = true
  try {
    const res = await request.post('/checkin')
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

const themeDisplayName = (theme) => ({ sakura: '粉色樱落', cyberpunk: '赛博魅紫', 'mojito-green': '莫兰迪绿', 'apple-light': '极简明亮', 'deep-ocean': '深邃之海' }[theme.id] || theme.name)

const changeTheme = (themeId) => {
  const theme = applyTheme(themeId)
  ElMessage.success(`已切换至「${themeDisplayName(theme)}」主题`)
}

const handleMenuCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'favorites':
      router.push('/favorites')
      break
    case 'notifications':
      router.push('/notifications')
      break
    case 'tools':
      router.push('/tools')
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
  ).then(async () => {
    await userStore.logout()
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
</script>

<style lang="scss">
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--tm-bg-page);
  color: var(--tm-text-primary);
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
  position: relative;
}

/* 顶部导航栏 */
.navbar {
  height: 64px;
  background: var(--tm-sidebar-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--tm-border-light);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 40px;
}

.logo {
  text-decoration: none;
  display: flex;
  align-items: center;
}

.logo-text {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: var(--tm-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-menu {
  display: flex;
  gap: 8px;
}

.nav-item {
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 15px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  transition: all 0.3s;
  position: relative;
}

.nav-item:hover, .nav-item.is-active {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.nav-item.is-active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: var(--tm-color-primary);
  border-radius: 2px;
}

.desktop-engine { display:flex;align-items:center;gap:6px;font-size:12px;color:#b42318;padding:6px 10px;border:1px solid var(--tm-border-light);border-radius:20px;background:var(--tm-card-bg); }
.desktop-engine.ready { color:#28724f; }
.desktop-engine i { width:7px;height:7px;border-radius:50%;background:currentColor; }

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 移动端汉堡菜单按钮 */
.nav-burger {
  display: none;
  font-size: 22px;
  cursor: pointer;
  color: var(--text-primary);
  align-items: center;
}

/* 响应式：768px 以下导航栏转汉堡菜单 */
@media (max-width: 768px) {
  .container {
    padding: 0 14px;
  }
  .nav-left {
    gap: 12px;
  }
  .nav-burger {
    display: flex;
  }
  .nav-menu {
    position: absolute;
    top: var(--tm-navbar-height, 64px);
    left: 0;
    right: 0;
    flex-direction: column;
    gap: 4px;
    padding: 12px 16px;
    background: var(--tm-sidebar-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--tm-border-light);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    transform: translateY(-8px);
    opacity: 0;
    pointer-events: none;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s;
    z-index: 99;
  }
  .nav-menu.open {
    transform: translateY(0);
    opacity: 1;
    pointer-events: auto;
  }
  .nav-item {
    padding: 12px 16px;
    width: 100%;
    border-radius: var(--radius-md);
  }
  .nav-right {
    gap: 8px;
  }
}

.theme-btn {
  font-size: 20px !important;
  color: var(--text-secondary) !important;
  transition: color 0.3s, filter 0.3s;
}

.theme-btn:hover {
  color: var(--tm-color-primary) !important;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s;
}

.user-info:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  border-color: rgba(var(--tm-color-primary-rgb), 0.2);
}

/* 主体布局 */
.layout-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  width: 100%;
  padding: 20px 24px;
  gap: 20px;
  align-items: stretch;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--tm-card-bg);
  border: 1px solid var(--tm-border-light);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px 12px;
}

.sidebar-scroll::-webkit-scrollbar {
  width: 4px;
}

.sidebar-group {
  margin-bottom: 24px;
}

.sidebar-label {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 12px;
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.sidebar-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  margin-bottom: 2px;
  transition: all 0.2s ease;
  position: relative;
  cursor: pointer;
}

.sidebar-icon {
  margin-right: 10px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.sidebar-icon .el-icon {
  font-size: 16px;
}

.sidebar-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.sidebar-item:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.04);
}

.sidebar-item:hover .sidebar-icon {
  background: rgba(var(--tm-color-primary-rgb), 0.12);
  color: var(--tm-color-primary);
}

.sidebar-item.active {
  color: var(--tm-color-primary);
  background: rgba(var(--tm-color-primary-rgb), 0.1);
  font-weight: 600;
}

.sidebar-item.active .sidebar-icon {
  background: rgba(var(--tm-color-primary-rgb), 0.18);
  color: var(--tm-color-primary);
}

.sidebar-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--tm-color-primary);
  border-radius: 0 3px 3px 0;
}

.sidebar-badge {
  margin-left: auto;
}

/* 主内容区 */
.main-content-with-sidebar {
  flex: 1;
  min-width: 0;
  min-height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  border-radius: var(--radius-lg);
  background: var(--tm-bg-page);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 页脚 */
.footer {
  padding: 24px 0;
  text-align: center;
  color: var(--text-muted);
  border-top: 1px solid rgba(255,255,255,0.05);
  background: var(--tm-card-bg);
}

/* 签到弹窗发光特效 */
:deep(.el-dialog) {
  background: var(--tm-card-bg) !important;
  border: 1px solid var(--tm-border-light);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
  border-radius: var(--radius-lg);
}
:deep(.el-dialog__title) {
  color: var(--tm-text-primary);
  font-weight: 700;
}

.checkin-content {
  text-align: center;
}

.checkin-streak {
  margin-bottom: 24px;
}

.streak-number {
  font-size: 56px;
  font-weight: 800;
  color: var(--tm-color-primary);
  line-height: 1;
}

.streak-label {
  font-size: 16px;
  color: var(--text-secondary);
  margin-top: 8px;
  letter-spacing: 2px;
}

.checkin-calendar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 20px;
  background: var(--tm-card-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--tm-border-light);
}

.calendar-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
  transition: all 0.3s;
}

.calendar-day.checked {
  opacity: 1;
}

.day-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--tm-card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  border: 1px solid var(--tm-border-light);
  transition: all 0.3s;
}

.calendar-day.checked .day-dot {
  background: rgba(var(--tm-color-primary-rgb), 0.2);
  color: var(--accent-primary);
  border-color: var(--accent-primary);
  box-shadow: 0 0 15px rgba(var(--tm-color-primary-rgb), 0.3);
}

.day-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.checkin-reward {
  margin-bottom: 24px;
  color: var(--text-secondary);
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  padding: 10px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(var(--tm-color-primary-rgb), 0.2);
}

.checkin-reward strong {
  color: var(--tm-color-primary);
  font-size: 18px;
  text-shadow: 0 0 8px rgba(var(--tm-color-primary-rgb), 0.3);
}

.checkin-btn {
  width: 100%;
  border-radius: 30px;
  font-size: 16px;
  letter-spacing: 2px;
  height: 48px;
}

/* 后台页面高度适配 */
.admin-page {
  height: 100vh;
  overflow: hidden;
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
