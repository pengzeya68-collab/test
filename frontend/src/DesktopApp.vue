<template>
  <el-config-provider :locale="zhCn">
    <router-view v-if="isAuthPage" />
    <div v-else class="desktop-app" :class="{ collapsed }">
      <aside class="desktop-sidebar">
        <div class="brand">
          <div class="brand-mark">TM</div>
          <div v-if="!collapsed" class="brand-copy"><strong>TestMaster</strong><span>自动化测试平台</span></div>
        </div>
        <nav class="nav-scroll">
          <section v-for="group in navigation" :key="group.label" class="nav-group">
            <div v-if="!collapsed" class="nav-label">{{ group.label }}</div>
            <router-link v-for="item in group.items" :key="item.path" :to="item.path" class="nav-item" :title="item.name">
              <el-icon><component :is="item.icon" /></el-icon><span v-if="!collapsed">{{ item.name }}</span>
            </router-link>
          </section>
        </nav>
        <button class="collapse-button" :title="collapsed ? '展开导航' : '收起导航'" @click="collapsed = !collapsed">
          <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon><span v-if="!collapsed">收起导航</span>
        </button>
      </aside>

      <div class="desktop-main">
        <header class="desktop-header">
          <div class="module-heading"><h1>{{ route.meta.title }}</h1><p>{{ route.meta.subtitle }}</p></div>
          <div class="header-tools">
            <span class="status" :class="backendState"><i></i>{{ backendText }}</span>
            <span class="status" :class="{ online: desktopReady, offline: !desktopReady }"><i></i>{{ desktopReady ? '执行引擎正常' : '执行引擎未连接' }}</span>
            <el-dropdown trigger="click" @command="changeTheme">
              <el-button class="icon-button" text title="切换主题"><el-icon><Brush /></el-icon></el-button>
              <template #dropdown><el-dropdown-menu><el-dropdown-item v-for="theme in themes" :key="theme.id" :command="theme.id"><i class="theme-dot" :style="{ background: theme.primary }"></i>{{ themeNames[theme.id] }}</el-dropdown-item></el-dropdown-menu></template>
            </el-dropdown>
            <el-dropdown @command="handleUserCommand">
              <button class="user-button"><span class="avatar">{{ userInitial }}</span><span>{{ userName }}</span><el-icon><ArrowDown /></el-icon></button>
              <template #dropdown><el-dropdown-menu><el-dropdown-item command="refresh">检查服务</el-dropdown-item><el-dropdown-item divided command="logout">退出登录</el-dropdown-item></el-dropdown-menu></template>
            </el-dropdown>
          </div>
        </header>
        <main class="desktop-workspace">
          <router-view v-slot="{ Component }"><component :is="Component" /></router-view>
        </main>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { ArrowDown, Brush, Coin, Collection, Connection, DataAnalysis, Document, Expand, Files, Fold, MagicStick, Monitor, Operation, Platform, SetUp, Suitcase, TrendCharts } from '@element-plus/icons-vue'
import { themes, applyTheme } from '@/utils/ThemeConfig'
import { useUserStore } from '@/stores/user'
import { uiAutomationApi } from '@/api/ui-automation'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(localStorage.getItem('desktop-sidebar-collapsed') === 'true')
const backendState = ref('checking')
const isAuthPage = computed(() => route.path === '/login')
const desktopReady = computed(() => typeof window.testmaster?.execution?.runCase === 'function')
const userName = computed(() => userStore.userInfo?.username || userStore.userInfo?.name || '测试用户')
const userInitial = computed(() => userName.value.slice(0, 1).toUpperCase())
const backendText = computed(() => ({ online: '服务正常', offline: '服务未连接', checking: '正在检查服务' }[backendState.value]))
const themeNames = { sakura: '樱花粉', cyberpunk: '赛博紫', 'mojito-green': '莫兰迪绿', 'apple-light': '极简明亮', 'deep-ocean': '深海暗色' }
const navigation = [
  { label: '工作台', items: [
    { path: '/auto-test', name: '自动化总览', icon: Platform },
    { path: '/cases', name: '接口自动化', icon: Connection },
    { path: '/ui-automation/cases', name: 'UI 自动化用例', icon: Monitor },
    { path: '/ui-automation/suites', name: 'UI 回归套件', icon: Suitcase },
  ]},
  { label: '接口资产', items: [
    { path: '/scenarios', name: '业务场景', icon: Operation },
    { path: '/suites', name: '接口回归套件', icon: Collection },
    { path: '/data-factory', name: '测试数据工厂', icon: Coin },
    { path: '/mock-service', name: 'Mock 服务', icon: SetUp },
  ]},
  { label: '质量工具', items: [
    { path: '/jmeter-assistant', name: 'JMeter 性能助手', icon: TrendCharts },
    { path: '/ai-generate-cases', name: 'AI 用例生成', icon: MagicStick },
    { path: '/test-coverage', name: '测试覆盖率', icon: DataAnalysis },
    { path: '/api-docs', name: 'API 文档', icon: Document },
    { path: '/backup-manager', name: '资产备份', icon: Files },
    { path: '/tools', name: '测试工具箱', icon: SetUp },
  ]},
]

async function checkBackend() {
  backendState.value = 'checking'
  try { await uiAutomationApi.health(); backendState.value = 'online' } catch { backendState.value = 'offline' }
}
function changeTheme(id) { applyTheme(id) }
async function handleUserCommand(command) {
  if (command === 'refresh') return checkBackend()
  if (command === 'logout') { await userStore.logout(); router.replace('/login') }
}
watch(collapsed, value => localStorage.setItem('desktop-sidebar-collapsed', String(value)))
onMounted(() => {
  const saved = localStorage.getItem('testmaster-theme') || 'apple-light'
  applyTheme(themes.some(theme => theme.id === saved) ? saved : 'apple-light')
  checkBackend()
})
</script>

<style scoped>
.desktop-app{display:grid;grid-template-columns:232px minmax(0,1fr);height:100vh;overflow:hidden;background:var(--bg-base);color:var(--text-primary);transition:grid-template-columns .2s}.desktop-app.collapsed{grid-template-columns:68px minmax(0,1fr)}
.desktop-sidebar{display:flex;min-height:0;flex-direction:column;background:var(--tm-sidebar-bg);border-right:1px solid var(--border-subtle);backdrop-filter:blur(18px)}
.brand{height:60px;display:flex;align-items:center;gap:11px;padding:0 15px;border-bottom:1px solid var(--border-subtle)}.brand-mark{width:36px;height:36px;flex:none;display:grid;place-items:center;border-radius:7px;background:var(--accent-primary);color:#fff;font-size:13px;font-weight:800}.brand-copy{display:flex;min-width:0;flex-direction:column}.brand-copy strong{font-size:15px}.brand-copy span{margin-top:2px;color:var(--text-secondary);font-size:11px}
.nav-scroll{flex:1;overflow:auto;padding:12px 9px}.nav-group+.nav-group{margin-top:16px}.nav-label{padding:0 10px 6px;color:var(--text-muted);font-size:11px;font-weight:600}.nav-item{height:38px;display:flex;align-items:center;gap:11px;padding:0 11px;border-radius:6px;color:var(--text-secondary);text-decoration:none;font-size:13px;white-space:nowrap}.nav-item:hover{background:var(--bg-surface-hover);color:var(--text-primary)}.nav-item.router-link-active{background:var(--accent-glow);color:var(--accent-primary);font-weight:600}.nav-item .el-icon{width:18px;font-size:17px}
.collapse-button{height:44px;display:flex;align-items:center;gap:11px;padding:0 24px;border:0;border-top:1px solid var(--border-subtle);background:transparent;color:var(--text-secondary);cursor:pointer;white-space:nowrap}.collapse-button:hover{color:var(--text-primary);background:var(--bg-surface-hover)}
.desktop-main{display:grid;grid-template-rows:60px minmax(0,1fr);min-width:0;min-height:0}.desktop-header{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:0 20px;background:var(--bg-elevated);border-bottom:1px solid var(--border-subtle)}.module-heading{min-width:0}.module-heading h1{margin:0;font-size:17px;line-height:1.25;letter-spacing:0}.module-heading p{margin:3px 0 0;color:var(--text-secondary);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.header-tools{display:flex;align-items:center;gap:10px;flex:none}.status{display:flex;align-items:center;gap:6px;color:var(--text-secondary);font-size:11px;white-space:nowrap}.status i{width:7px;height:7px;border-radius:50%;background:#9ca3af}.status.online i{background:#16a34a}.status.offline i{background:#dc2626}.status.checking i{background:#d97706}.icon-button{width:34px;height:34px;font-size:17px}.user-button{height:36px;display:flex;align-items:center;gap:7px;padding:0 8px;border:0;background:transparent;color:var(--text-primary);cursor:pointer}.avatar{width:27px;height:27px;display:grid;place-items:center;border-radius:50%;background:var(--accent-primary);color:#fff;font-size:12px;font-weight:700}.theme-dot{width:10px;height:10px;border-radius:50%;margin-right:9px}.desktop-workspace{min-width:0;min-height:0;overflow:auto;background:var(--tm-bg-color);padding:16px}.desktop-workspace>:deep(*){box-sizing:border-box}
@media(max-width:900px){.desktop-app{grid-template-columns:68px minmax(0,1fr)}.brand-copy,.nav-label,.nav-item span,.collapse-button span{display:none}.header-tools .status{display:none}.desktop-workspace{padding:10px}}
</style>
