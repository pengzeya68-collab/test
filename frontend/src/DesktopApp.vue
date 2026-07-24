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
            <el-select
              v-if="projects.length"
              v-model="activeProjectId"
              class="project-switcher"
              size="small"
              placeholder="选择项目"
              @change="onProjectChange"
            >
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
            <span class="status" :class="backendState"><i></i>{{ backendText }}</span>
            <span class="status" :class="{ online: desktopReady, offline: !desktopReady }"><i></i>{{ desktopReady ? '执行引擎正常' : '执行引擎未连接' }}</span>
            <button class="status agent-status" :class="agentStatusClass" title="桌面 Agent 设置" @click="openAgentDialog"><i></i>{{ agentStatusText }}</button>
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
          <div v-if="workspaceLoading" class="workspace-loading"><el-icon class="is-loading"><Loading /></el-icon><span>正在加载工作区</span></div>
          <router-view v-else v-slot="{ Component }"><component :is="Component" :key="`${route.fullPath}:${activeProjectId || 'default'}`" /></router-view>
        </main>
      </div>
    </div>
    <el-dialog v-model="agentDialogVisible" title="无人值守桌面 Agent" width="520px" :close-on-click-modal="false">
      <div class="agent-summary">
        <div><span>当前状态</span><strong :class="agentStatusClass">{{ agentStatusText }}</strong></div>
        <div v-if="agentStatus.registered"><span>Agent 标识</span><code>{{ agentStatus.agentKey || `#${agentStatus.agentId}` }}</code></div>
        <div v-if="agentStatus.activeRunId"><span>正在执行</span><strong>运行 #{{ agentStatus.activeRunId }}</strong></div>
        <div v-if="agentStatus.lastHeartbeatAt"><span>最后心跳</span><strong>{{ formatAgentTime(agentStatus.lastHeartbeatAt) }}</strong></div>
      </div>
      <el-alert v-if="agentStatus.lastError" :title="agentStatus.lastError" type="error" show-icon :closable="false" />
      <el-alert v-if="usingInsecureRemoteAgentEndpoint" class="agent-http-warning" title="当前企业服务使用 HTTP 连接" description="桌面 Agent 可以注册并执行任务，但访问令牌和运行数据不具备 HTTPS 传输保护。正式环境请尽快为该服务配置 HTTPS。" type="warning" show-icon :closable="false" />
      <el-form label-position="top" class="agent-form">
        <el-form-item label="Agent 名称">
          <el-input v-model="agentForm.name" maxlength="200" placeholder="例如：测试部 Windows 执行机" />
        </el-form-item>
        <el-form-item label="企业服务地址">
          <el-input v-model="agentForm.serverUrl" placeholder="https://testmaster.example.com" />
        </el-form-item>
        <el-form-item label="无人值守登录态">
          <el-select v-model="agentForm.authStateId" clearable placeholder="不使用已保存登录态" style="width:100%">
            <el-option v-for="item in authStates" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <div class="form-hint">登录态由系统加密保存；需要验证码的网站先在录制器中登录并保存登录态。</div>
        </el-form-item>
        <el-form-item label="运行方式">
          <el-switch v-model="agentForm.headless" active-text="后台无界面运行" inactive-text="显示浏览器窗口" />
        </el-form-item>
        <el-form-item label="并行度">
          <el-input-number v-model="agentForm.maxParallel" :min="1" :max="16" />
          <div class="form-hint">同一 Agent 可并行领取的运行数（需后端 max_parallel 同步）。</div>
        </el-form-item>
        <el-form-item label="浏览器引擎">
          <el-select v-model="agentForm.browserEngine" style="width:100%">
            <el-option label="Chromium" value="chromium" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="WebKit" value="webkit" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="agentStatus.registered" type="danger" plain :disabled="agentBusy || agentStatus.state === 'running'" @click="removeAgent">移除</el-button>
        <span class="dialog-spacer"></span>
        <el-button v-if="agentStatus.registered && agentStatus.enabled" :loading="agentBusy" @click="disableAgent">停用</el-button>
        <el-button v-else-if="agentStatus.registered" type="success" :loading="agentBusy" @click="enableAgent">启用</el-button>
        <el-button type="primary" :loading="agentBusy" :disabled="!desktopReady || agentStatus.state === 'running'" @click="registerAgent">{{ agentStatus.registered ? '重新注册' : '注册并启用' }}</el-button>
      </template>
    </el-dialog>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Bell, Brush, Coin, Collection, Connection, DataAnalysis, Document, Expand, Files, Fold, Loading, MagicStick, Monitor, Operation, Platform, SetUp, Share, Suitcase, Timer, TrendCharts, Warning } from '@element-plus/icons-vue'
import { themes, applyTheme } from '@/utils/ThemeConfig'
import { useUserStore } from '@/stores/user'
import { uiAutomationApi } from '@/api/ui-automation'
import { workspaceApi, getActiveProjectId } from '@/api/workspace'
import { useProjectStore } from '@/stores/project'
import { getServerUrl, setServerUrl } from '@/utils/server-config'
import { DESKTOP_NAVIGATION } from '@/constants/desktop-navigation'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(localStorage.getItem('desktop-sidebar-collapsed') === 'true')
const backendState = ref('checking')
const isAuthPage = computed(() => route.path === '/login')
const desktopReady = computed(() => typeof window.testmaster?.execution?.runCase === 'function')
const emptyAgentStatus = { state: 'unregistered', registered: false, enabled: false, agentId: null, agentKey: null, name: null, serverUrl: null, authStateId: null, headless: true, maxParallel: 1, browserEngine: 'chromium', activeRunId: null, activeRunIds: [], lastHeartbeatAt: null, lastError: null }
const agentStatus = ref({ ...emptyAgentStatus })
const agentDialogVisible = ref(false)
const agentBusy = ref(false)
const authStates = ref([])
let removeAgentStatusListener = null
const userName = computed(() => userStore.userInfo?.username || userStore.userInfo?.name || '测试用户')
const agentForm = ref({ name: `${userName.value || 'TestMaster'} 的执行机`, serverUrl: getServerUrl(), authStateId: null, headless: true, maxParallel: 1, browserEngine: 'chromium' })
const userInitial = computed(() => userName.value.slice(0, 1).toUpperCase())
const backendText = computed(() => ({ online: '服务正常', offline: '服务未连接', checking: '正在检查服务' }[backendState.value]))
const agentStatusText = computed(() => ({
  unregistered: 'Agent 未注册', disabled: 'Agent 已停用', starting: 'Agent 启动中', online: 'Agent 在线',
  running: `Agent 执行中${agentStatus.value.activeRunId ? ` #${agentStatus.value.activeRunId}` : ''}`,
  offline: 'Agent 离线重试', error: 'Agent 异常', stopping: 'Agent 正在停止',
}[agentStatus.value.state] || 'Agent 状态未知'))
const agentStatusClass = computed(() => ({
  online: ['online', 'running'].includes(agentStatus.value.state),
  checking: ['starting', 'stopping'].includes(agentStatus.value.state),
  offline: ['unregistered', 'disabled', 'offline', 'error'].includes(agentStatus.value.state),
  running: agentStatus.value.state === 'running',
}))
const usingInsecureRemoteAgentEndpoint = computed(() => {
  try {
    const url = new URL(agentForm.value.serverUrl)
    return url.protocol === 'http:' && !['127.0.0.1', 'localhost'].includes(url.hostname)
  } catch { return false }
})
const themeNames = {
  'professional-dark': '专业深色',
  cyberpunk: '赛博魅紫',
  'deep-ocean': '深邃之海',
  sakura: '粉色樱落',
  'mojito-green': '莫兰迪绿',
  'professional-light': '专业浅色',
  'apple-light': '极简明亮'
}
const iconMap = {
  Platform, Connection, Monitor, Suitcase, Collection, DataAnalysis, Document, Timer,
  MagicStick, Share, Operation, Coin, SetUp, TrendCharts, Warning, Files, Bell,
}
const navigation = DESKTOP_NAVIGATION.map((group) => ({
  label: group.label,
  items: group.items.map((item) => ({
    ...item,
    icon: iconMap[item.icon] || Platform,
  })),
}))
const projectStore = useProjectStore()
const projects = ref([])
const activeProjectId = ref(getActiveProjectId())
const workspaceLoading = ref(true)

async function loadProjects() {
  workspaceLoading.value = true
  try {
    const data = await workspaceApi.listProjects()
    projects.value = data?.items || []
    const preferred = getActiveProjectId() || data?.active_project_id
    if (preferred && projects.value.some((p) => p.id === preferred)) {
      activeProjectId.value = preferred
      projectStore.setProjectId(preferred)
    } else if (projects.value.length) {
      activeProjectId.value = projects.value[0].id
      projectStore.setProjectId(projects.value[0].id)
    }
  } catch {
    projects.value = []
  } finally {
    workspaceLoading.value = false
  }
}

function onProjectChange(id) {
  activeProjectId.value = id
  projectStore.setProjectId(id)
}

async function checkBackend() {
  backendState.value = 'checking'
  try { await uiAutomationApi.health(); backendState.value = 'online' } catch { backendState.value = 'offline' }
}
async function refreshAgentStatus() {
  if (!window.testmaster?.agent) return
  try { agentStatus.value = await window.testmaster.agent.status() }
  catch (error) { agentStatus.value = { ...emptyAgentStatus, state: 'error', lastError: error.message || String(error) } }
}
async function openAgentDialog() {
  await refreshAgentStatus()
  try { authStates.value = await window.testmaster?.authStates?.list?.() || [] } catch { authStates.value = [] }
  agentForm.value = {
    name: agentStatus.value.name || `${userName.value || 'TestMaster'} 的执行机`,
    serverUrl: agentStatus.value.serverUrl || getServerUrl(),
    authStateId: agentStatus.value.authStateId || null,
    headless: agentStatus.value.headless !== false,
    maxParallel: agentStatus.value.maxParallel || 1,
    browserEngine: agentStatus.value.browserEngine || 'chromium',
  }
  agentDialogVisible.value = true
}
async function registerAgent() {
  const accessToken = localStorage.getItem('token') || ''
  if (!accessToken) return ElMessage.error('登录状态已失效，请重新登录后注册 Agent')
  agentBusy.value = true
  try {
    const serverUrl = setServerUrl(agentForm.value.serverUrl)
    agentForm.value.serverUrl = serverUrl
    agentStatus.value = await window.testmaster.agent.register({ ...agentForm.value, serverUrl, accessToken })
    ElMessage.success('桌面 Agent 已注册并开始接收任务')
  } catch (error) { ElMessage.error(formatAgentError(error, 'Agent 注册失败')) }
  finally { agentBusy.value = false }
}
async function enableAgent() {
  agentBusy.value = true
  try { agentStatus.value = await window.testmaster.agent.enable(); ElMessage.success('桌面 Agent 已启用') }
  catch (error) { ElMessage.error(error.message || 'Agent 启用失败') }
  finally { agentBusy.value = false }
}
async function disableAgent() {
  if (agentStatus.value.state === 'running') {
    try { await ElMessageBox.confirm('停用会取消当前无人值守任务，确定继续吗？', '停用桌面 Agent', { type: 'warning' }) }
    catch { return }
  }
  agentBusy.value = true
  try { agentStatus.value = await window.testmaster.agent.disable(); ElMessage.success('桌面 Agent 已停用') }
  catch (error) { ElMessage.error(error.message || 'Agent 停用失败') }
  finally { agentBusy.value = false }
}
async function removeAgent() {
  try { await ElMessageBox.confirm('移除后需要重新登录并注册，确定继续吗？', '移除桌面 Agent', { type: 'warning' }) }
  catch { return }
  agentBusy.value = true
  try { agentStatus.value = await window.testmaster.agent.remove(); ElMessage.success('本机 Agent 凭据已移除') }
  catch (error) { ElMessage.error(error.message || 'Agent 移除失败') }
  finally { agentBusy.value = false }
}
function formatAgentTime(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString('zh-CN', { hour12: false })
}
function formatAgentError(error, fallback) {
  const message = error?.message || String(error || '')
  const knownMessages = {
    AGENT_NAME_REQUIRED: '请填写 Agent 名称',
    LOGIN_REQUIRED: '登录状态已失效，请重新登录后注册 Agent',
    INVALID_SERVER_URL: '企业服务地址格式不正确，请填写完整的 HTTP 或 HTTPS 地址',
    'Failed to fetch': '无法连接企业服务，请确认地址、网络和服务器状态',
    'fetch failed': '无法连接企业服务，请确认地址、网络和服务器状态',
  }
  return knownMessages[message] || message || fallback
}
function changeTheme(id) { applyTheme(id) }
async function handleUserCommand(command) {
  if (command === 'refresh') return checkBackend()
  if (command === 'logout') { await userStore.logout(); router.replace('/login') }
}
watch(collapsed, value => localStorage.setItem('desktop-sidebar-collapsed', String(value)))
watch(isAuthPage, (authPage) => {
  if (!authPage) loadProjects()
})
onMounted(() => {
  checkBackend()
  refreshAgentStatus()
  if (!isAuthPage.value) loadProjects()
  window.addEventListener('testmaster-projects-changed', loadProjects)
  if (window.testmaster?.agent?.onStatus) removeAgentStatusListener = window.testmaster.agent.onStatus(status => { agentStatus.value = status })
})
onUnmounted(() => {
  window.removeEventListener('testmaster-projects-changed', loadProjects)
  if (typeof removeAgentStatusListener === 'function') removeAgentStatusListener()
})
</script>

<style scoped>
.desktop-app{display:grid;grid-template-columns:232px minmax(0,1fr);height:100vh;overflow:hidden;background:var(--bg-base);color:var(--text-primary);transition:grid-template-columns .2s}.desktop-app.collapsed{grid-template-columns:68px minmax(0,1fr)}
.desktop-sidebar{display:flex;min-height:0;flex-direction:column;background:var(--tm-sidebar-bg);border-right:1px solid var(--border-subtle);backdrop-filter:blur(18px)}
.brand{height:60px;display:flex;align-items:center;gap:11px;padding:0 15px;border-bottom:1px solid var(--border-subtle)}.brand-mark{width:36px;height:36px;flex:none;display:grid;place-items:center;border-radius:7px;background:var(--accent-primary);color:#fff;font-size:13px;font-weight:800}.brand-copy{display:flex;min-width:0;flex-direction:column}.brand-copy strong{font-size:15px}.brand-copy span{margin-top:2px;color:var(--text-secondary);font-size:11px}
.nav-scroll{flex:1;overflow:auto;padding:12px 9px}.nav-group+.nav-group{margin-top:16px}.nav-label{padding:0 10px 6px;color:var(--text-muted);font-size:11px;font-weight:600}.nav-item{height:38px;display:flex;align-items:center;gap:11px;padding:0 11px;border-radius:6px;color:var(--text-secondary);text-decoration:none;font-size:13px;white-space:nowrap}.nav-item:hover{background:var(--bg-surface-hover);color:var(--text-primary)}.nav-item.router-link-active{background:var(--accent-glow);color:var(--accent-primary);font-weight:600}.nav-item .el-icon{width:18px;font-size:17px}
.collapse-button{height:44px;display:flex;align-items:center;gap:11px;padding:0 24px;border:0;border-top:1px solid var(--border-subtle);background:transparent;color:var(--text-secondary);cursor:pointer;white-space:nowrap}.collapse-button:hover{color:var(--text-primary);background:var(--bg-surface-hover)}
.desktop-main{display:grid;grid-template-rows:60px minmax(0,1fr);min-width:0;min-height:0}.desktop-header{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:0 20px;background:var(--bg-elevated);border-bottom:1px solid var(--border-subtle)}.module-heading{min-width:0}.module-heading h1{margin:0;font-size:17px;line-height:1.25;letter-spacing:0}.module-heading p{margin:3px 0 0;color:var(--text-secondary);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.header-tools{display:flex;align-items:center;gap:10px;flex:none}.project-switcher{width:160px}.status{display:flex;align-items:center;gap:6px;color:var(--text-secondary);font-size:11px;white-space:nowrap}.status i{width:7px;height:7px;border-radius:50%;background:#9ca3af}.status.online i{background:var(--tm-color-success)}.status.offline i{background:var(--tm-color-danger)}.status.checking i{background:var(--tm-color-warning)}.icon-button{width:34px;height:34px;font-size:17px}.user-button{height:36px;display:flex;align-items:center;gap:7px;padding:0 8px;border:0;background:transparent;color:var(--text-primary);cursor:pointer}.avatar{width:27px;height:27px;display:grid;place-items:center;border-radius:50%;background:var(--accent-primary);color:#fff;font-size:12px;font-weight:700}.theme-dot{width:10px;height:10px;border-radius:50%;margin-right:9px}.desktop-workspace{min-width:0;min-height:0;overflow:auto;background:var(--tm-bg-color);padding:16px}.desktop-workspace>:deep(*){box-sizing:border-box}
.workspace-loading{min-height:220px;display:flex;align-items:center;justify-content:center;gap:9px;color:var(--text-secondary);font-size:13px}.agent-status{border:0;background:transparent;padding:5px 2px;cursor:pointer}.agent-status:hover{color:var(--accent-primary)}.status.running i{box-shadow:0 0 0 4px color-mix(in srgb,var(--tm-color-success) 18%,transparent)}
.agent-summary{display:grid;grid-template-columns:1fr 1fr;gap:10px 20px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--border-subtle)}.agent-summary div{display:flex;min-width:0;flex-direction:column;gap:4px}.agent-summary span{font-size:12px;color:var(--text-secondary)}.agent-summary strong,.agent-summary code{overflow:hidden;text-overflow:ellipsis;font-size:13px;color:var(--text-primary)}.agent-summary strong.online{color:#15803d}.agent-summary strong.offline{color:#b91c1c}.agent-http-warning{margin-bottom:12px}.agent-form{margin-top:14px}.form-hint{margin-top:5px;color:var(--text-muted);font-size:11px;line-height:1.5}.dialog-spacer{flex:1}:deep(.el-dialog__footer){display:flex;align-items:center}
@media(max-width:900px){.desktop-app{grid-template-columns:68px minmax(0,1fr)}.brand-copy,.nav-label,.nav-item span,.collapse-button span{display:none}.header-tools .status{display:none}.desktop-workspace{padding:10px}}
</style>
