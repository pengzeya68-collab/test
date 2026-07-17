import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const secured = (title, subtitle) => ({ requiresAuth: true, title, subtitle })
const routes = [
  { path: '/', redirect: '/auto-test' },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  { path: '/auto-test', name: 'AutoTest', component: () => import('@/views/AutoTest.vue'), meta: secured('自动化工作台', '统一管理接口、场景、UI 与性能测试资产') },
  { path: '/cases', name: 'CaseList', component: () => import('@/views/CaseList.vue'), meta: secured('接口用例', '设计、调试并维护可复用的接口测试用例') },
  { path: '/scenarios', name: 'ScenarioList', component: () => import('@/views/ScenarioList.vue'), meta: secured('业务场景', '编排跨接口的长流程业务验证') },
  { path: '/suites', name: 'SuiteManager', component: () => import('@/views/SuiteManager.vue'), meta: secured('接口回归套件', '组织批量执行、环境与回归策略') },
  { path: '/data-factory', name: 'DataFactory', component: () => import('@/views/DataFactory.vue'), meta: secured('测试数据工厂', '生成和维护自动化所需的测试数据') },
  { path: '/mock-service', name: 'MockService', component: () => import('@/views/MockService.vue'), meta: secured('Mock 服务', '模拟依赖服务与异常响应') },
  { path: '/backup-manager', name: 'BackupManager', component: () => import('@/views/BackupManager.vue'), meta: secured('资产备份', '备份、恢复和迁移自动化测试资产') },
  { path: '/ui-automation/cases', name: 'UICaseList', component: () => import('@/views/ui-automation/UICaseList.vue'), meta: secured('UI 自动化用例', '录制、编辑、调试并执行真实浏览器操作') },
  { path: '/ui-automation/suites', name: 'UISuiteManager', component: () => import('@/views/ui-automation/UISuiteManager.vue'), meta: secured('UI 回归套件', '编排数据驱动的端到端回归任务') },
  { path: '/ui-automation/cases/:id', name: 'UICaseEditor', component: () => import('@/views/ui-automation/UICaseEditor.vue'), meta: secured('UI 用例编辑器', '编辑步骤、定位器、断言和运行配置') },
  { path: '/jmeter-assistant', name: 'JmeterAssistant', component: () => import('@/views/JmeterAssistant.vue'), meta: secured('JMeter 性能助手', '配置与执行性能测试任务') },
  { path: '/ai-generate-cases', name: 'AIGenerateCases', component: () => import('@/views/AIGenerateCases.vue'), meta: secured('AI 用例生成', '根据需求辅助生成结构化测试用例') },
  { path: '/test-coverage', name: 'TestCoverage', component: () => import('@/views/TestCoverage.vue'), meta: secured('测试覆盖率', '分析需求、接口和用例的覆盖情况') },
  { path: '/api-docs', name: 'ApiDocs', component: () => import('@/views/ApiDocs.vue'), meta: secured('API 文档', '查看和维护接口定义') },
  { path: '/api-doc-preview', name: 'ApiDocPreview', component: () => import('@/views/ApiDocPreview.vue'), meta: secured('API 文档预览', '预览接口文档发布效果') },
  { path: '/tools', name: 'TestingTools', component: () => import('@/views/TestingTools.vue'), meta: secured('测试工具箱', '常用测试、编码和数据处理工具') },
  { path: '/profile', redirect: '/auto-test' },
  { path: '/favorites', redirect: '/auto-test' },
  { path: '/notifications', redirect: '/auto-test' },
  { path: '/:pathMatch(.*)*', redirect: '/auto-test' },
]

const router = createRouter({ history: createWebHashHistory(), routes })
router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.requiresAuth && !store.isLoggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.path === '/login' && store.isLoggedIn) return '/auto-test'
  return true
})
router.afterEach((to) => { document.title = `${to.meta.title || '工作台'} - TestMaster Desktop` })
export default router
