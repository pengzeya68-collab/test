<template>
  <div class="admin-layout">
    <!-- 移动端遮罩 -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false" />

    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, 'mobile-open': sidebarOpen }">
      <div class="logo" @click="$router.push('/admin/dashboard')">
        <span class="logo-icon">TM</span>
        <span v-if="!sidebarCollapsed" class="logo-text">Admin</span>
      </div>

      <nav class="menu">
        <div
          v-for="menu in menus"
          :key="menu.path"
          class="menu-item"
          :class="{ active: isActive(menu.path) }"
          :title="sidebarCollapsed ? menu.title : ''"
          @click="handleMenuClick(menu.path)"
        >
          <span class="menu-icon">{{ menu.icon }}</span>
          <span v-if="!sidebarCollapsed" class="menu-title">{{ menu.title }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="collapse-btn" @click="toggleCollapse" :title="sidebarCollapsed ? '展开' : '收起'">
          <span class="collapse-icon">{{ sidebarCollapsed ? '▶' : '◀' }}</span>
          <span v-if="!sidebarCollapsed" class="collapse-text">收起菜单</span>
        </div>
      </div>
    </aside>

    <!-- 右侧内容 -->
    <main class="main-content">
      <!-- 顶部导航 -->
      <header class="top-nav">
        <div class="nav-left">
          <button class="hamburger" @click="sidebarOpen = !sidebarOpen">
            <span></span><span></span><span></span>
          </button>
          <h2 class="page-title">{{ currentTitle }}</h2>
        </div>
        <div class="nav-right">
          <el-dropdown trigger="click" @command="changeTheme">
            <button class="nav-btn theme-btn">
              <span class="btn-icon">🎨</span>
              <span class="btn-text">主题</span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="theme in themes" :key="theme.id" :command="theme.id">
                  <span class="theme-dot" :style="{ background: theme.primary }" />
                  {{ theme.name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <div class="user-badge">
            <span class="user-avatar">{{ (adminInfo?.username || 'A')[0].toUpperCase() }}</span>
            <span class="user-name">{{ adminInfo?.username || 'Admin' }}</span>
          </div>
          <button class="nav-btn logout-btn" @click="logout">退出</button>
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
import { ElMessageBox, ElMessage } from 'element-plus'
import { themes, applyTheme, loadSavedTheme } from '@/utils/ThemeConfig'
import { useAdminStore } from '@/stores/admin'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const adminInfo = computed(() => adminStore.adminInfo)
const sidebarCollapsed = ref(false)
const sidebarOpen = ref(false)

const menus = [
  { path: '/admin/dashboard', title: '数据统计', icon: '📊' },
  { path: '/admin/exercises', title: '习题管理', icon: '📝' },
  { path: '/admin/paths', title: '学习路径', icon: '🗺️' },
  { path: '/admin/users', title: '用户管理', icon: '👥' },
  { path: '/admin/exams', title: '考试管理', icon: '📋' },
  { path: '/admin/interview', title: '面试题库', icon: '🎤' },
  { path: '/admin/community', title: '社区管理', icon: '💬' },
  { path: '/admin/backup', title: '备份管理', icon: '💾' },
  { path: '/admin/ai-config', title: 'AI配置', icon: '🤖' },
  { path: '/admin/settings', title: '系统设置', icon: '⚙️' },
]

const isActive = (path) => route.path.startsWith(path)

const currentTitle = computed(() => {
  const menu = menus.find(m => route.path.startsWith(m.path))
  return menu ? menu.title : '后台管理'
})

const handleMenuClick = (path) => {
  router.push(path)
  sidebarOpen.value = false
}

const toggleCollapse = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('admin_sidebar_collapsed', sidebarCollapsed.value)
}

const changeTheme = (themeId) => {
  const theme = applyTheme(themeId)
  ElMessage.success(`已切换至「${theme.name}」主题`)
}

onMounted(() => {
  const savedThemeId = loadSavedTheme()
  applyTheme(savedThemeId)
  const saved = localStorage.getItem('admin_sidebar_collapsed')
  if (saved === 'true') sidebarCollapsed.value = true
})

const logout = async () => {
  await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  await adminStore.clearAdminInfo()
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  width: 100%;
  display: flex;
  background: var(--tm-bg-color);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--tm-sidebar-bg);
  border-right: var(--tm-card-border);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, min-width 0.25s ease;
  z-index: 100;
}
.sidebar.collapsed {
  width: 64px;
  min-width: 64px;
}

/* Logo */
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  cursor: pointer;
  flex-shrink: 0;
}
.logo-icon {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 1px;
}
.logo-text {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
}

/* 菜单 */
.menu {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
  overflow-x: hidden;
}
.menu::-webkit-scrollbar { width: 4px; }
.menu::-webkit-scrollbar-thumb { background: var(--tm-border-light); border-radius: 2px; }

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--tm-text-secondary);
  font-size: 14px;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
}
.menu-item:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  color: var(--tm-color-primary);
}
.menu-item.active {
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  box-shadow: 0 2px 8px rgba(var(--tm-color-primary-rgb), 0.3);
}
.menu-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}
.menu-title {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 折叠按钮 */
.sidebar-footer {
  padding: 8px;
  border-top: 1px solid var(--tm-border-light);
  flex-shrink: 0;
}
.collapse-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--tm-text-secondary);
  font-size: 13px;
  transition: all 0.2s;
}
.collapse-btn:hover {
  background: rgba(var(--tm-color-primary-rgb), 0.08);
  color: var(--tm-color-primary);
}
.collapse-icon {
  font-size: 12px;
  flex-shrink: 0;
}

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 顶部导航 */
.top-nav {
  height: 56px;
  background: var(--tm-card-bg);
  border-bottom: var(--tm-card-border);
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text-primary);
}

/* 汉堡按钮 (移动端) */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  background: none;
  border: none;
  cursor: pointer;
}
.hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--tm-text-primary);
  border-radius: 1px;
  transition: all 0.2s;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--tm-border-light);
  background: transparent;
  color: var(--tm-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.nav-btn:hover {
  border-color: var(--tm-color-primary);
  color: var(--tm-color-primary);
}
.btn-icon { font-size: 14px; }

.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tm-color-primary), var(--tm-color-primary-dark));
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name {
  color: var(--tm-text-primary);
  font-size: 13px;
  font-weight: 500;
}

.logout-btn {
  color: var(--tm-color-danger, #f56c6c);
  border-color: transparent;
}
.logout-btn:hover {
  background: rgba(245, 108, 108, 0.08);
  border-color: rgba(245, 108, 108, 0.3);
}

.theme-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
  border: 1px solid rgba(255,255,255,0.2);
}

/* 内容区域 */
.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}
.content-area::-webkit-scrollbar { width: 6px; }
.content-area::-webkit-scrollbar-thumb { background: var(--tm-border-light); border-radius: 3px; }
.content-area::-webkit-scrollbar-thumb:hover { background: var(--tm-color-primary); }

/* ===== 移动端遮罩 ===== */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 99;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .hamburger {
    display: flex;
  }
  .sidebar {
    position: fixed;
    left: -220px;
    top: 0;
    bottom: 0;
    transition: left 0.25s ease;
  }
  .sidebar.mobile-open {
    left: 0;
  }
  .sidebar-overlay {
    display: block;
  }
  .btn-text {
    display: none;
  }
  .user-name {
    display: none;
  }
}
</style>
