<template>
  <section class="desktop-dashboard">
    <div class="dashboard-topbar">
      <div>
        <h2>今天的测试工作</h2>
        <p>从一个明确的工作区开始，不在首页加载编辑器或重复导航。</p>
      </div>
      <el-button :loading="checking" plain @click="refreshStatus">
        <el-icon><Refresh /></el-icon>刷新状态
      </el-button>
    </div>

    <section class="status-strip" aria-label="运行状态">
      <div class="status-cell">
        <el-icon class="status-icon service"><Connection /></el-icon>
        <div><span>企业服务</span><strong :class="serviceState">{{ serviceText }}</strong></div>
      </div>
      <div class="status-cell">
        <el-icon class="status-icon engine"><Monitor /></el-icon>
        <div><span>本机执行引擎</span><strong :class="engineReady ? 'online' : 'offline'">{{ engineReady ? '可执行 UI 自动化' : '尚未连接' }}</strong></div>
      </div>
      <div class="status-cell">
        <el-icon class="status-icon browser"><ChromeFilled /></el-icon>
        <div><span>浏览器执行</span><strong :class="engineReady ? 'online' : 'muted'">{{ engineReady ? '由桌面端管理' : '连接执行引擎后可用' }}</strong></div>
      </div>
    </section>

    <div class="content-grid">
      <section class="workspace-section">
        <div class="section-heading"><div><h3>开始工作</h3><p>按测试类型进入独立工作区</p></div></div>
        <div class="workspace-grid">
          <button v-for="item in primaryWorkspaces" :key="item.path" class="workspace-entry" @click="go(item.path)">
            <span class="entry-icon" :class="item.tone"><el-icon><component :is="item.icon" /></el-icon></span>
            <span class="entry-copy"><strong>{{ item.name }}</strong><small>{{ item.description }}</small></span>
            <el-icon class="entry-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
      </section>

      <section class="activity-section">
        <div class="section-heading"><div><h3>执行准备</h3><p>运行前先确认依赖状态</p></div></div>
        <div class="readiness-list">
          <div class="readiness-row"><span class="readiness-dot" :class="serviceState"></span><span>服务连通性</span><strong>{{ serviceText }}</strong></div>
          <div class="readiness-row"><span class="readiness-dot" :class="engineReady ? 'online' : 'offline'"></span><span>桌面执行引擎</span><strong>{{ engineReady ? '已就绪' : '待注册或启动' }}</strong></div>
          <div class="readiness-row"><span class="readiness-dot muted"></span><span>当前工作区</span><strong>工作概览</strong></div>
        </div>
        <div class="activity-actions">
          <el-button type="primary" @click="go('/ui-automation/cases')">录制 UI 用例</el-button>
          <el-button @click="go('/cases')">创建接口用例</el-button>
        </div>
      </section>
    </div>

    <section class="tools-section">
      <div class="section-heading"><div><h3>测试资产与工具</h3><p>按需进入，首页不预加载这些功能</p></div></div>
      <div class="tool-links">
        <button v-for="item in toolLinks" :key="item.path" @click="go(item.path)"><el-icon><component :is="item.icon" /></el-icon>{{ item.name }}</button>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ChromeFilled, Collection, Connection, DataAnalysis, Document, Monitor, Operation, Refresh, SetUp, Suitcase } from '@element-plus/icons-vue'
import { uiAutomationApi } from '@/api/ui-automation'

const router = useRouter()
const checking = ref(false)
const serviceState = ref('checking')
const engineReady = computed(() => typeof window.testmaster?.execution?.runCase === 'function')
const serviceText = computed(() => ({ online: '服务正常', offline: '服务未连接', checking: '正在检测' }[serviceState.value]))

const primaryWorkspaces = [
  { path: '/dashboard', name: '概览', description: '工作状态与通知入口', icon: Monitor, tone: 'blue' },
  { path: '/api-debugger', name: '接口调试', description: '调试、用例与文档', icon: Connection, tone: 'violet' },
  { path: '/scenarios', name: '自动化', description: '场景、套件与契约', icon: Operation, tone: 'green' },
  { path: '/ui-automation/cases', name: 'UI 自动化', description: '用例、元素与自愈', icon: Suitcase, tone: 'orange' },
  { path: '/traffic-workbench', name: '流量与 Mock', description: '流量分析与 Mock', icon: Connection, tone: 'blue' },
  { path: '/ui-automation/shards', name: '执行与报告', description: '分片、Flaky 与缺陷', icon: DataAnalysis, tone: 'violet' },
  { path: '/workspace-projects', name: '管理', description: '项目、备份与工具', icon: SetUp, tone: 'green' },
]
const toolLinks = [
  { path: '/cases', name: '接口用例', icon: Collection },
  { path: '/suites', name: '接口回归套件', icon: Collection },
  { path: '/ui-automation/elements', name: '元素仓库', icon: Collection },
  { path: '/mock-service', name: 'Mock 服务', icon: Connection },
  { path: '/notification-center', name: '任务通知', icon: Document },
  { path: '/api-docs', name: 'API 文档', icon: Document },
]

function go(path) { router.push(path) }
async function refreshStatus() {
  checking.value = true
  serviceState.value = 'checking'
  try { await uiAutomationApi.health(); serviceState.value = 'online' }
  catch { serviceState.value = 'offline' }
  finally { checking.value = false }
}

onMounted(refreshStatus)
</script>

<style scoped>
.desktop-dashboard{max-width:1440px;margin:0 auto;padding:4px;color:var(--text-primary)}
.dashboard-topbar{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding:8px 0 20px}.dashboard-topbar h2{margin:0;font-size:20px;line-height:1.3}.dashboard-topbar p,.section-heading p{margin:5px 0 0;color:var(--text-secondary);font-size:12px;line-height:1.5}
.status-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--border-subtle);background:var(--bg-elevated)}.status-cell{display:flex;align-items:center;gap:11px;min-width:0;padding:15px 17px}.status-cell+.status-cell{border-left:1px solid var(--border-subtle)}.status-icon{width:34px;height:34px;display:grid;place-items:center;border-radius:6px;font-size:17px}.status-icon.service{background:color-mix(in srgb,var(--tm-color-success) 14%,transparent);color:var(--tm-color-success)}.status-icon.engine{background:color-mix(in srgb,var(--accent-primary) 14%,transparent);color:var(--accent-primary)}.status-icon.browser{background:color-mix(in srgb,var(--tm-color-warning) 14%,transparent);color:var(--tm-color-warning)}.status-cell div{display:flex;min-width:0;flex-direction:column;gap:3px}.status-cell span{color:var(--text-secondary);font-size:11px}.status-cell strong{overflow:hidden;text-overflow:ellipsis;font-size:13px;white-space:nowrap}.online{color:var(--tm-color-success)}.offline{color:var(--tm-color-danger)}.checking{color:var(--tm-color-warning)}.muted{color:var(--text-secondary)}
.content-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(310px,.85fr);gap:16px;margin-top:16px}.workspace-section,.activity-section,.tools-section{border:1px solid var(--border-subtle);background:var(--bg-elevated)}.workspace-section,.activity-section{padding:18px}.section-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.section-heading h3{margin:0;font-size:14px;line-height:1.3}
.workspace-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:16px}.workspace-entry{display:flex;align-items:center;gap:11px;min-width:0;min-height:78px;padding:13px;border:1px solid var(--border-subtle);border-radius:6px;background:var(--bg-surface);color:var(--text-primary);cursor:pointer;text-align:left;transition:border-color .16s ease,background .16s ease}.workspace-entry:hover{border-color:var(--accent-primary);background:var(--bg-surface-hover)}.entry-icon{width:35px;height:35px;display:grid;place-items:center;flex:none;border-radius:6px;font-size:17px}.entry-icon.blue{color:#1976d2;background:color-mix(in srgb,#1976d2 13%,transparent)}.entry-icon.violet{color:var(--accent-primary);background:var(--accent-glow)}.entry-icon.green{color:var(--tm-color-success);background:color-mix(in srgb,var(--tm-color-success) 13%,transparent)}.entry-icon.orange{color:var(--tm-color-warning);background:color-mix(in srgb,var(--tm-color-warning) 13%,transparent)}.entry-copy{display:flex;min-width:0;flex:1;flex-direction:column;gap:4px}.entry-copy strong{font-size:13px}.entry-copy small{overflow:hidden;color:var(--text-secondary);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.entry-arrow{flex:none;color:var(--text-muted);font-size:16px}
.readiness-list{margin-top:16px;border-top:1px solid var(--border-subtle)}.readiness-row{display:grid;grid-template-columns:8px minmax(0,1fr) auto;align-items:center;gap:9px;min-height:45px;border-bottom:1px solid var(--border-subtle);font-size:12px}.readiness-dot{width:7px;height:7px;border-radius:50%;background:var(--text-muted)}.readiness-dot.online{background:var(--tm-color-success)}.readiness-dot.offline{background:var(--tm-color-danger)}.readiness-dot.checking{background:var(--tm-color-warning)}.readiness-row span:not(.readiness-dot){color:var(--text-secondary)}.readiness-row strong{font-size:12px;font-weight:600}.activity-actions{display:flex;gap:8px;margin-top:16px}.activity-actions .el-button{margin:0;flex:1}
.tools-section{margin-top:16px;padding:18px}.tool-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}.tool-links button{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 10px;border:1px solid var(--border-subtle);border-radius:5px;background:var(--bg-surface);color:var(--text-secondary);cursor:pointer;font-size:12px}.tool-links button:hover{border-color:var(--accent-primary);color:var(--accent-primary);background:var(--bg-surface-hover)}
@media(max-width:1050px){.content-grid{grid-template-columns:1fr}.activity-section{display:grid;grid-template-columns:1fr 1fr;gap:0 24px}.activity-section .section-heading{grid-column:1/-1}.activity-actions{align-self:end}}@media(max-width:700px){.desktop-dashboard{padding:0}.dashboard-topbar{padding-top:2px}.dashboard-topbar p{display:none}.status-strip,.workspace-grid{grid-template-columns:1fr}.status-cell+.status-cell{border-top:1px solid var(--border-subtle);border-left:0}.activity-section{display:block}.workspace-section,.activity-section,.tools-section{padding:14px}.dashboard-topbar h2{font-size:17px}}
</style>
