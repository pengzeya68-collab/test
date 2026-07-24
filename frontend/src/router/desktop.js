import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const secured = (title, subtitle) => ({ requiresAuth: true, title, subtitle })
const legacyAutoTestRedirect = (to) => {
  const targetByTab = {
    debug: '/api-debugger',
    interfaces: '/cases',
    scenario: '/scenarios',
    scenarios: '/scenarios',
    suites: '/suites',
    data: '/data-factory',
    mock: '/mock-service',
    jmeter: '/jmeter-assistant',
    ui: '/ui-automation/cases',
    'ui-suites': '/ui-automation/suites',
  }
  const query = { ...to.query }
  const tab = query.tab
  const scenarioId = query.scenarioId || query.id
  const path = (tab === 'scenario' || tab === 'scenarios') && scenarioId
    ? `/scenarios/${encodeURIComponent(String(scenarioId))}`
    : (targetByTab[tab] || '/dashboard')
  delete query.tab
  delete query.scenarioId
  delete query.id
  return { path, query }
}
const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  { path: '/dashboard', name: 'DesktopDashboard', component: () => import('@/views/DesktopDashboard.vue'), meta: secured('工作概览', '查看服务状态、执行环境和常用测试工作入口') },
  { path: '/workspace-projects', name: 'WorkspaceProjects', component: () => import('@/views/WorkspaceProjects.vue'), meta: secured('项目', '管理工作区项目与成员，资产按项目隔离') },
  { path: '/api-debugger', name: 'ApiDebugger', component: () => import('@/views/ApiDebugger.vue'), meta: secured('接口调试', '发送请求、检查响应并将接口沉淀为测试用例') },
  // Historical deep links remain usable, but the old combined web workspace is
  // deliberately not embedded in the desktop shell.
  { path: '/auto-test', redirect: legacyAutoTestRedirect },
  { path: '/cases', name: 'CaseList', component: () => import('@/views/CaseList.vue'), meta: secured('接口用例', '设计、调试并维护可复用的接口测试用例') },
  { path: '/scenarios', name: 'ScenarioList', component: () => import('@/views/ScenarioList.vue'), meta: secured('业务场景', '编排跨接口的长流程业务验证') },
  { path: '/scenarios/:scenarioId', name: 'ScenarioEditor', component: () => import('@/views/ScenarioEditor.vue'), props: true, meta: secured('场景编辑器', '添加步骤、配置数据驱动并调试业务场景') },
  { path: '/suites', name: 'SuiteManager', component: () => import('@/views/SuiteManager.vue'), meta: secured('接口回归套件', '组织批量执行、环境与回归策略') },
  { path: '/data-factory', name: 'DataFactory', component: () => import('@/views/DataFactory.vue'), meta: secured('测试数据工厂', '生成和维护自动化所需的测试数据') },
  { path: '/import-center', name: 'ImportCenter', component: () => import('@/views/ImportCenter.vue'), meta: secured('流量导入中心', '将浏览器录制流量筛选、映射并沉淀为接口和场景资产') },
  { path: '/traffic-workbench', name: 'TrafficWorkbench', component: () => import('@/views/TrafficWorkbench.vue'), meta: secured('流量工作台', '分析已脱敏流量，并人工确认转换为接口和业务场景') },
  { path: '/notification-center', name: 'NotificationCenter', component: () => import('@/views/NotificationCenter.vue'), meta: secured('任务通知中心', '配置长时间任务的外部结果通知和投递审计') },
  { path: '/mock-service', name: 'MockService', component: () => import('@/views/MockService.vue'), meta: secured('Mock 服务', '模拟依赖服务与异常响应') },
  { path: '/backup-manager', name: 'BackupManager', component: () => import('@/views/BackupManager.vue'), meta: secured('资产备份', '备份、恢复和迁移自动化测试资产') },
  { path: '/ui-automation/cases', name: 'UICaseList', component: () => import('@/views/ui-automation/UICaseList.vue'), meta: secured('UI 自动化用例', '录制、编辑、调试并执行真实浏览器操作') },
  { path: '/ui-automation/suites', name: 'UISuiteManager', component: () => import('@/views/ui-automation/UISuiteManager.vue'), meta: secured('UI 回归套件', '编排数据驱动的端到端回归任务') },
  { path: '/ui-automation/cases/:id', name: 'UICaseEditor', component: () => import('@/views/ui-automation/UICaseEditor.vue'), meta: secured('UI 用例编辑器', '编辑步骤、定位器、断言和运行配置') },
  { path: '/ui-automation/elements', name: 'ElementRepository', component: () => import('@/views/ui-automation/ElementRepository.vue'), meta: secured('元素仓库', '集中管理页面对象与定位器，支持 AI 自愈') },
  { path: '/ui-automation/flaky', name: 'FlakyDashboard', component: () => import('@/views/ui-automation/FlakyDashboard.vue'), meta: secured('Flaky 检测', '识别不稳定用例并支持隔离') },
  { path: '/ui-automation/visual', name: 'VisualDashboard', component: () => import('@/views/ui-automation/VisualDashboard.vue'), meta: secured('视觉回归', '基线管理与截图对比审核') },
  { path: '/ui-automation/defects', name: 'DefectCenter', component: () => import('@/views/ui-automation/DefectCenter.vue'), meta: secured('缺陷中心', '失败一键建缺陷并同步 Tracker') },
  { path: '/ui-automation/traces', name: 'TraceViewer', component: () => import('@/views/ui-automation/TraceViewer.vue'), meta: secured('Trace Viewer', '查看 Playwright Trace 会话与时间线') },
  { path: '/ui-automation/healing', name: 'HealingHistory', component: () => import('@/views/ui-automation/HealingHistory.vue'), meta: secured('自愈历史', '审核定位器自愈建议') },
  { path: '/ui-automation/network-rules', name: 'NetworkRules', component: () => import('@/views/ui-automation/NetworkRules.vue'), meta: secured('网络拦截', '配置请求拦截与 Mock 规则') },
  { path: '/ui-automation/contracts', name: 'ContractTesting', component: () => import('@/views/ui-automation/ContractTesting.vue'), meta: secured('契约测试', 'OpenAPI 快照、变更与校验') },
  { path: '/ui-automation/health', name: 'APIHealth', component: () => import('@/views/ui-automation/APIHealth.vue'), meta: secured('API 健康', '接口可用性监控') },
  { path: '/ui-automation/reviews', name: 'ReviewCenter', component: () => import('@/views/ui-automation/ReviewCenter.vue'), meta: secured('评审与覆盖', '用例评审、需求追溯与报告') },
  { path: '/ui-automation/flow', name: 'FlowEditor', component: () => import('@/views/ui-automation/FlowEditor.vue'), meta: secured('流程编排', '场景流程图节点与边编辑') },
  { path: '/ui-automation/shards', name: 'ShardProgress', component: () => import('@/views/ui-automation/ShardProgress.vue'), meta: secured('分片进度', '套件并行分片执行看板') },
  { path: '/ui-automation/protocols', name: 'ProtocolDebugger', component: () => import('@/views/ui-automation/ProtocolDebugger.vue'), meta: secured('协议调试', 'gRPC / WebSocket / SSE') },
  { path: '/jmeter-assistant', name: 'JmeterAssistant', component: () => import('@/views/JmeterAssistant.vue'), meta: secured('JMeter 性能助手', '配置与执行性能测试任务') },
  { path: '/ai-generate-cases', name: 'AIGenerateCases', component: () => import('@/views/AIGenerateCases.vue'), meta: secured('AI 用例生成', '根据需求辅助生成结构化测试用例') },
  { path: '/test-coverage', name: 'TestCoverage', component: () => import('@/views/TestCoverage.vue'), meta: secured('测试覆盖率', '分析需求、接口和用例的覆盖情况') },
  { path: '/api-docs', name: 'ApiDocs', component: () => import('@/views/ApiDocs.vue'), meta: secured('API 文档', '查看和维护接口定义') },
  { path: '/api-doc-preview', name: 'ApiDocPreview', component: () => import('@/views/ApiDocPreview.vue'), meta: secured('API 文档预览', '预览接口文档发布效果') },
  { path: '/tools', name: 'TestingTools', component: () => import('@/views/TestingTools.vue'), meta: secured('测试工具箱', '常用测试、编码和数据处理工具') },
  { path: '/profile', redirect: '/dashboard' },
  { path: '/favorites', redirect: '/dashboard' },
  { path: '/notifications', redirect: '/dashboard' },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({ history: createWebHashHistory(), routes })
router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.requiresAuth && !store.isLoggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.path === '/login' && store.isLoggedIn) return '/dashboard'
  return true
})
router.afterEach((to) => { document.title = `${to.meta.title || '工作台'} - TestMaster Desktop` })
export default router
