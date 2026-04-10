<template>
  <div class="admin-layout-dark">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <h1>TestMaster</h1>
        <span class="badge">Admin</span>
      </div>
      <nav class="menu">
        <div
          v-for="menu in menus"
          :key="menu.path"
          class="menu-item"
          :class="{ active: $route.path === menu.path }"
          @click="$router.push(menu.path)"
        >
          <span class="menu-title">{{ menu.title }}</span>
        </div>
      </nav>
    </aside>

    <!-- 右侧内容 -->
    <main class="main-content">
      <!-- 顶部导航 -->
      <header class="top-nav">
        <div class="page-title">
          <h2>{{ currentTitle }}</h2>
        </div>
        <div class="user-info">
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
          <span class="user-name">{{ adminInfo?.username || 'Admin' }}</span>
          <el-button type="text" class="logout-btn" @click="logout">退出登录</el-button>
        </div>
      </header>

      <!-- 主内容 -->
      <div class="content-area">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Brush, ArrowDown } from '@element-plus/icons-vue'
import { themes, applyTheme, loadSavedTheme } from '@/utils/ThemeConfig'

const route = useRoute()
const router = useRouter()

const adminInfo = ref(null)

const menus = [
  { path: '/admin/dashboard', title: '数据统计' },
  { path: '/admin/exercises', title: '习题管理' },
  { path: '/admin/paths', title: '学习路径' },
  { path: '/admin/users', title: '用户管理' },
  { path: '/admin/exams', title: '考试管理' },
  { path: '/admin/interview', title: '面试题库' },
  { path: '/admin/community', title: '社区管理' },
  { path: '/admin/backup', title: '备份管理' },
  { path: '/admin/settings', title: '系统设置' }
]

const currentTitle = computed(() => {
  const menu = menus.find(m => m.path === route.path)
  return menu ? menu.title : '后台管理'
})

const changeTheme = (themeId) => {
  const theme = applyTheme(themeId)
  ElMessage.success(`已切换至「${theme.name}」主题`)
}

onMounted(() => {
  const info = localStorage.getItem('admin_info')
  if (info) {
    try {
      adminInfo.value = JSON.parse(info)
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }
  // 加载保存的主题
  const savedThemeId = loadSavedTheme()
  applyTheme(savedThemeId)
})

const logout = async () => {
  await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })

  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
  ElMessage.success('退出成功')
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout-dark {
  height: 100vh;
  width: 100%;
  display: flex;
  background: var(--tm-bg-color);
  background-image: var(--tm-bg-image);
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background: var(--tm-sidebar-bg);
  border-right: var(--tm-card-border);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 4px 0 15px rgba(0, 0, 0, 0.2);
}

.logo {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: linear-gradient(135deg, var(--tm-color-primary) 0%, var(--tm-color-primary-dark) 100%);
  border-bottom: var(--tm-card-border);
}

.logo h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: white;
  letter-spacing: 1px;
}

.logo .badge {
  font-size: 11px;
  opacity: 0.8;
  color: white;
  margin-top: 4px;
}

.menu {
  padding: 16px 12px;
  flex: 1;
}

.menu-item {
  padding: 14px 18px;
  margin-bottom: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  border-radius: 8px;
  color: var(--tm-text-secondary);
  font-size: 15px;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.menu-item:hover {
  background: rgba(var(--tm-color-primary), 0.1);
  border-color: rgba(var(--tm-color-primary), 0.3);
  color: var(--tm-color-primary);
  transform: translateX(4px);
}

.menu-item.active {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  border-color: var(--tm-color-primary);
  color: white;
  box-shadow: 0 4px 12px var(--tm-glow-effect);
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-nav {
  height: 70px;
  background: var(--tm-card-bg);
  border-bottom: var(--tm-card-border);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.page-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--tm-color-primary);
  font-size: 14px;
  padding: 6px 12px;
  border: 1px solid rgba(var(--tm-color-primary), 0.3);
  border-radius: 6px;
}

.theme-btn:hover {
  background: rgba(var(--tm-color-primary), 0.1);
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

.user-name {
  color: var(--tm-text-secondary);
  font-size: 14px;
}

.logout-btn {
  color: #ff6b6b;
  font-size: 14px;
}

.logout-btn:hover {
  color: #ff8787;
  background: rgba(255, 107, 107, 0.1);
}

.content-area {
  flex: 1;
  padding: 20px;
  background: transparent;
  overflow-y: auto;
}

/* 滚动条美化 */
.content-area::-webkit-scrollbar {
  width: 8px;
}

.content-area::-webkit-scrollbar-track {
  background: rgba(var(--tm-bg-page-rgb), 0.5);
}

.content-area::-webkit-scrollbar-thumb {
  background: var(--tm-border-light);
  border-radius: 4px;
}

.content-area::-webkit-scrollbar-thumb:hover {
  background: var(--tm-color-primary);
}
</style>
