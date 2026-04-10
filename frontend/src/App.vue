<template>
  <div id="app">
    <!-- 导航栏 -->
    <el-header class="navbar" v-if="!isAuthPage">
      <div class="container">
        <div class="nav-left">
          <router-link to="/" class="logo">
            <span class="logo-text">TestMaster</span>
          </router-link>
          <div class="nav-menu">
            <router-link to="/" class="nav-item" :class="{ 'is-active': activeMenu === '/' }">首页</router-link>
            <router-link to="/learning-paths" class="nav-item" :class="{ 'is-active': activeMenu === '/learning-paths' }">学习路径</router-link>
            <router-link to="/exercises" class="nav-item" :class="{ 'is-active': activeMenu === '/exercises' }">习题库</router-link>
            <router-link to="/code-playground" class="nav-item" :class="{ 'is-active': activeMenu === '/code-playground' }">代码练习室</router-link>
            <router-link to="/auto-test" class="nav-item" :class="{ 'is-active': activeMenu === '/auto-test' }">自动化测试</router-link>
            <router-link to="/interview" class="nav-item" :class="{ 'is-active': activeMenu === '/interview' }">面试系统</router-link>
            <router-link to="/ai-tutor" class="nav-item" :class="{ 'is-active': activeMenu === '/ai-tutor' }">AI导师</router-link>
            <router-link to="/skill-analysis" class="nav-item" :class="{ 'is-active': activeMenu === '/skill-analysis' }">技能分析</router-link>
            <router-link to="/community" class="nav-item" :class="{ 'is-active': activeMenu === '/community' }">社区</router-link>
            <router-link to="/exams" class="nav-item" :class="{ 'is-active': activeMenu === '/exams' }">模考大赛</router-link>
          </div>
        </div>
        <div class="nav-right">
          <!-- 美化中心主题切换 -->
          <el-dropdown trigger="click" @command="changeTheme">
            <el-button type="text" class="theme-btn">
              <el-icon><Brush /></el-icon>
              <span>美化中心</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
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
            <el-dropdown @command="handleMenuCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                <span class="username">{{ userInfo?.username }}</span>
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="my-learning">我的学习</el-dropdown-item>
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
    </el-header>

    <!-- 主内容 -->
    <main class="main-content">
      <router-view :key="$route.fullPath" />
    </main>

    <!-- 页脚 -->
    <footer class="footer" v-if="!isAuthPage">
      <div class="container">
        <p>© 2026 TestMaster 测试工程师成长平台</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, ArrowDown, Brush } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { themes, loadSavedTheme, applyTheme } from '@/utils/ThemeConfig'

const router = useRouter()
const route = useRoute()

const isLoggedIn = ref(false)
const userInfo = ref(null)

// 是否是登录注册页面或后台页面
const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register' || route.path.startsWith('/admin')
})

// 当前激活的菜单
const activeMenu = computed(() => {
  return route.path
})

onMounted(() => {
  checkLoginStatus()
  // 加载保存的主题 - 全站生效
  const savedThemeId = loadSavedTheme()
  applyTheme(savedThemeId)
})

// 监听路由变化，每次页面跳转时重新检查登录状态
watch(
  () => route.path,
  () => {
    checkLoginStatus()
  }
)

// 检查登录状态
const checkLoginStatus = () => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  if (token && userStr) {
    isLoggedIn.value = true
    userInfo.value = JSON.parse(userStr)
  } else {
    isLoggedIn.value = false
    userInfo.value = null
  }
}

// 主题切换
const changeTheme = (themeId) => {
  const theme = applyTheme(themeId)
  ElMessage.success(`已切换至「${theme.name}」主题`)
}

// 处理下拉菜单命令
const handleMenuCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'my-learning':
      ElMessage.info('我的学习页面开发中')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
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
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    isLoggedIn.value = false
    userInfo.value = null
    ElMessage.success('退出登录成功')
    router.push('/login')
  }).catch(() => {
    // 取消
  })
}

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

// 处理菜单点击
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
  background: var(--tm-bg-card);
  box-shadow: var(--tm-shadow-base);
  height: 64px;
  line-height: 64px;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid var(--tm-border-light);
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
  background: linear-gradient(135deg, var(--tm-color-primary) 0%, #667eea 100%);
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
  background: rgba(24, 144, 255, 0.04);
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
  background: rgba(24, 144, 255, 0.08);
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
  background: var(--tm-bg-card);
  padding: 24px 0;
  text-align: center;
  color: var(--tm-text-secondary);
  font-size: 13px;
  border-top: 1px solid var(--tm-border-light);
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
  border: 1px solid rgba(var(--tm-color-primary), 0.3);
  border-radius: 6px;
  transition: all 0.2s;
}

.theme-btn:hover {
  background: rgba(var(--tm-color-primary), 0.08);
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
