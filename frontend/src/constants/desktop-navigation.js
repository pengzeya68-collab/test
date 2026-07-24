/**
 * Desktop shell navigation — Phase A: ≤7 top-level workspaces.
 * Icons are string keys resolved by DesktopApp.vue.
 */
export const DESKTOP_NAVIGATION = [
  {
    label: '概览',
    items: [
      { path: '/dashboard', name: '工作概览', icon: 'Platform' },
      { path: '/notification-center', name: '任务通知', icon: 'Bell' },
    ],
  },
  {
    label: 'API 资产',
    items: [
      { path: '/api-debugger', name: '接口调试', icon: 'Connection' },
      { path: '/cases', name: '接口用例', icon: 'Collection' },
      { path: '/api-docs', name: 'API 文档', icon: 'Document' },
      { path: '/ai-generate-cases', name: 'AI 用例生成', icon: 'MagicStick' },
    ],
  },
  {
    label: '自动化',
    items: [
      { path: '/scenarios', name: '业务场景', icon: 'Operation' },
      { path: '/suites', name: '接口回归套件', icon: 'Collection' },
      { path: '/data-factory', name: '测试数据工厂', icon: 'Coin' },
      { path: '/ui-automation/health', name: 'API 健康', icon: 'TrendCharts' },
      { path: '/ui-automation/contracts', name: '契约测试', icon: 'Document' },
    ],
  },
  {
    label: 'UI 自动化',
    items: [
      { path: '/ui-automation/cases', name: 'UI 用例', icon: 'Monitor' },
      { path: '/ui-automation/suites', name: 'UI 回归套件', icon: 'Suitcase' },
      { path: '/ui-automation/elements', name: '元素仓库', icon: 'Collection' },
      { path: '/ui-automation/visual', name: '视觉回归', icon: 'Monitor' },
      { path: '/ui-automation/traces', name: 'Trace Viewer', icon: 'Timer' },
      { path: '/ui-automation/network-rules', name: '网络拦截', icon: 'Share' },
      { path: '/ui-automation/healing', name: '自愈历史', icon: 'MagicStick' },
    ],
  },
  {
    label: '流量与 Mock',
    items: [
      { path: '/traffic-workbench', name: '流量工作台', icon: 'Connection' },
      { path: '/import-center', name: '导入中心', icon: 'Files' },
      { path: '/mock-service', name: 'Mock 服务', icon: 'SetUp' },
    ],
  },
  {
    label: '执行与报告',
    items: [
      { path: '/ui-automation/shards', name: '分片进度', icon: 'Operation' },
      { path: '/ui-automation/flaky', name: 'Flaky 检测', icon: 'DataAnalysis' },
      { path: '/ui-automation/defects', name: '缺陷中心', icon: 'Document' },
      { path: '/ui-automation/reviews', name: '评审与覆盖', icon: 'Warning' },
      { path: '/test-coverage', name: '测试覆盖率', icon: 'DataAnalysis' },
      { path: '/jmeter-assistant', name: 'JMeter 性能', icon: 'TrendCharts' },
    ],
  },
  {
    label: '管理',
    items: [
      { path: '/workspace-projects', name: '项目', icon: 'Suitcase' },
      { path: '/backup-manager', name: '资产备份', icon: 'Files' },
      { path: '/tools', name: '测试工具箱', icon: 'SetUp' },
    ],
  },
]

export const DESKTOP_WORKSPACE_LABELS = DESKTOP_NAVIGATION.map((g) => g.label)
