// JMeter 节点类型定义 - 共享模块
// 合并自 JmeterAssistant.vue (63项) 与 JmeterTreeNode.vue (20项),去除大小写重复
// 规范:优先使用 JMeter 原生 tag 名(与后端 _JMX_TYPE_MAP 解析输出一致)

export const NODE_TYPES = {
  // ===== 容器 =====
  TestPlan: { label: '测试计划', icon: '📋', category: 'container' },
  ThreadGroup: { label: '线程组', icon: '👥', category: 'container', parent: 'TestPlan' },

  // ===== 采样器 =====
  HttpSampler: { label: 'HTTP 请求', icon: '🌐', category: 'sampler', parent: 'ThreadGroup' },
  JDBCSampler: { label: 'JDBC 请求', icon: '🗄️', category: 'sampler', parent: 'ThreadGroup' },
  DebugSampler: { label: '调试采样器', icon: '🐛', category: 'sampler', parent: 'ThreadGroup' },

  // ===== 控制器 =====
  IfController: { label: '如果(If)控制器', icon: '🔀', category: 'controller', parent: 'ThreadGroup' },
  LoopController: { label: '循环控制器', icon: '🔄', category: 'controller', parent: 'ThreadGroup' },
  WhileController: { label: 'While 控制器', icon: '🔁', category: 'controller', parent: 'ThreadGroup' },
  TransactionController: { label: '事务控制器', icon: '📦', category: 'controller', parent: 'ThreadGroup' },
  ThroughputController: { label: '吞吐量控制器', icon: '⏱️', category: 'controller', parent: 'ThreadGroup' },
  OnceOnlyController: { label: '仅一次控制器', icon: '1️⃣', category: 'controller', parent: 'ThreadGroup' },
  ForEachController: { label: 'ForEach 控制器', icon: '🔁', category: 'controller', parent: 'ThreadGroup' },
  SwitchController: { label: 'Switch 控制器', icon: '🔀', category: 'controller', parent: 'ThreadGroup' },
  RandomController: { label: '随机控制器', icon: '🎲', category: 'controller', parent: 'ThreadGroup' },
  InterleaveController: { label: '交替控制器', icon: '🔃', category: 'controller', parent: 'ThreadGroup' },
  IncludeController: { label: 'Include 控制器', icon: '📂', category: 'controller', parent: 'ThreadGroup' },
  ModuleController: { label: '模块控制器', icon: '🧩', category: 'controller', parent: 'ThreadGroup' },
  RunTimeController: { label: '运行时间控制器', icon: '⏱️', category: 'controller', parent: 'ThreadGroup' },

  // ===== 断言 =====
  ResponseAssertion: { label: '响应断言', icon: '✅', category: 'assertion', parent: 'HttpSampler' },
  DurationAssertion: { label: '持续时间断言', icon: '⏱️', category: 'assertion', parent: 'HttpSampler' },
  JSONPathAssertion: { label: 'JSON Path 断言', icon: '📋', category: 'assertion', parent: 'HttpSampler' },
  BeanShellAssertion: { label: 'BeanShell 断言', icon: '💻', category: 'assertion', parent: 'HttpSampler' },
  JSR223Assertion: { label: 'JSR223 断言', icon: '🔥', category: 'assertion', parent: 'HttpSampler' },
  SizeAssertion: { label: '响应大小断言', icon: '📏', category: 'assertion', parent: 'HttpSampler' },
  XPathAssertion: { label: 'XPath 断言', icon: '🗂️', category: 'assertion', parent: 'HttpSampler' },
  CompareAssertion: { label: '比较断言', icon: '⚖️', category: 'assertion', parent: 'HttpSampler' },
  XMLAssertion: { label: 'XML 断言', icon: '📜', category: 'assertion', parent: 'HttpSampler' },
  XPath2Assertion: { label: 'XPath2 断言', icon: '🗂️', category: 'assertion', parent: 'HttpSampler' },
  HTMLAssertion: { label: 'HTML 断言', icon: '📄', category: 'assertion', parent: 'HttpSampler' },
  MD5HexAssertion: { label: 'MD5 断言', icon: '🔐', category: 'assertion', parent: 'HttpSampler' },
  SMIMEAssertion: { label: 'SMIME 断言', icon: '📧', category: 'assertion', parent: 'HttpSampler' },

  // ===== 提取器 =====
  RegexExtractor: { label: '正则提取器', icon: '🔍', category: 'extractor', parent: 'HttpSampler' },
  JSONExtractor: { label: 'JSON 提取器', icon: '📤', category: 'extractor', parent: 'HttpSampler' },
  BoundaryExtractor: { label: '边界提取器', icon: '📐', category: 'extractor', parent: 'HttpSampler' },
  CSSSelectorExtractor: { label: 'CSS 选择器提取器', icon: '🎨', category: 'extractor', parent: 'HttpSampler' },
  XPathExtractor: { label: 'XPath 提取器', icon: '🗂️', category: 'extractor', parent: 'HttpSampler' },

  // ===== 定时器 =====
  ConstantTimer: { label: '固定定时器', icon: '⏰', category: 'timer', parent: 'HttpSampler' },
  UniformRandomTimer: { label: '均匀随机定时器', icon: '🎲', category: 'timer', parent: 'HttpSampler' },
  GaussianRandomTimer: { label: '高斯随机定时器', icon: '📊', category: 'timer', parent: 'HttpSampler' },
  SynchronizingTimer: { label: '同步定时器(集合点)', icon: '🔄', category: 'timer', parent: 'HttpSampler' },
  ConstantThroughputTimer: { label: '常数吞吐量定时器', icon: '📈', category: 'timer', parent: 'HttpSampler' },
  PoissonRandomTimer: { label: '泊松随机定时器', icon: '📊', category: 'timer', parent: 'HttpSampler' },

  // ===== 前后置处理器 =====
  BeanShellPreProcessor: { label: 'BeanShell 前置', icon: '⚙️', category: 'preprocessor', parent: 'HttpSampler' },
  BeanShellPostProcessor: { label: 'BeanShell 后置', icon: '⚙️', category: 'postprocessor', parent: 'HttpSampler' },
  JSR223PreProcessor: { label: 'JSR223 前置处理器', icon: '🔥', category: 'preprocessor', parent: 'HttpSampler' },
  JSR223PostProcessor: { label: 'JSR223 后置处理器', icon: '🔥', category: 'postprocessor', parent: 'HttpSampler' },
  UserParametersPreProcessor: { label: '用户参数前置处理器', icon: '👤', category: 'preprocessor', parent: 'HttpSampler' },
  SampleTimeout: { label: '采样超时', icon: '⏱️', category: 'preprocessor', parent: 'HttpSampler' },

  // ===== 配置 =====
  HttpHeaderManager: { label: 'HTTP 信息头管理器', icon: '📨', category: 'config', parent: 'ThreadGroup' },
  HTTPCookieManager: { label: 'HTTP Cookie 管理器', icon: '🍪', category: 'config', parent: 'ThreadGroup' },
  HttpCacheManager: { label: 'HTTP 缓存管理器', icon: '💾', category: 'config', parent: 'ThreadGroup' },
  HttpAuthManager: { label: 'HTTP 授权管理器', icon: '🔐', category: 'config', parent: 'ThreadGroup' },
  DNSCacheManager: { label: 'DNS 缓存管理器', icon: '🌐', category: 'config', parent: 'ThreadGroup' },
  HTTPRequestDefaults: { label: 'HTTP 请求默认值', icon: '🎯', category: 'config', parent: 'ThreadGroup' },
  CsvDataSource: { label: 'CSV 数据文件', icon: '📄', category: 'config', parent: 'ThreadGroup' },
  RandomVariableConfig: { label: '随机变量', icon: '🎲', category: 'config', parent: 'ThreadGroup' },
  UserParameters: { label: '用户参数(多账号)', icon: '👤', category: 'config', parent: 'ThreadGroup' },
  JDBCConnection: { label: 'JDBC 连接', icon: '🗄️', category: 'config', parent: 'TestPlan' },

  // ===== 监听器 =====
  ViewResultsTree: { label: '查看结果树', icon: '👁️', category: 'listener', parent: 'ThreadGroup' },
  SummaryReport: { label: '聚合报告', icon: '📈', category: 'listener', parent: 'ThreadGroup' },
  AggregateGraph: { label: '聚合图表', icon: '📉', category: 'listener', parent: 'ThreadGroup' },
  AggregateReport: { label: '聚合报告(高级)', icon: '📊', category: 'listener', parent: 'ThreadGroup' },
  ResponseTimeGraph: { label: '响应时间图', icon: '📉', category: 'listener', parent: 'ThreadGroup' },
  InfluxDBBackendListener: { label: 'InfluxDB 后端监听器', icon: '📡', category: 'listener', parent: 'TestPlan' },
  Summariser: { label: '汇总器', icon: '📊', category: 'listener', parent: 'TestPlan' },
  GraphListener: { label: '图形监听器', icon: '📈', category: 'listener', parent: 'ThreadGroup' },
}

// 别名映射:旧名称 → 规范名称
// 用于向后兼容(老脚本/老数据可能用旧名称)
export const TYPE_ALIASES = {
  // 大小写不一致
  HTTPHeaderManager: 'HttpHeaderManager',
  HttpCookieManager: 'HTTPCookieManager',
  // 命名不一致
  JsonAssertion: 'JSONPathAssertion',
  JsonExtractor: 'JSONExtractor',
  SyncTimer: 'SynchronizingTimer',
  CSVDataSet: 'CsvDataSource',
}

// 解析别名,返回规范类型名
export const resolveType = (type) => TYPE_ALIASES[type] || type

// 获取节点类型信息(自动解析别名)
export const nodeTypeInfo = (type) => {
  const resolved = resolveType(type)
  return NODE_TYPES[resolved] || null
}

// 生成新 UID
let _uidCounter = 0
export const newUid = () => {
  _uidCounter += 1
  return `jmeter_${Date.now()}_${_uidCounter.toString(36)}_${Math.random().toString(36).slice(2, 7)}`
}

// 递归重新分配 UID(深拷贝后调用,避免跨树复制时 UID 冲突)
export const reassignUids = (node) => {
  if (!node) return
  node.uid = newUid()
  if (Array.isArray(node.children)) {
    node.children.forEach(reassignUids)
  }
}

// ===== 父子关系合法性表 =====
// 用于拖拽放置校验:哪种类型可以放在哪种父节点下
export const VALID_CHILDREN = {
  TestPlan: [
    'ThreadGroup',
    'HttpHeaderManager', 'HTTPCookieManager', 'HttpCacheManager', 'HttpAuthManager', 'DNSCacheManager',
    'JDBCConnection', 'HTTPRequestDefaults', 'CsvDataSource', 'RandomVariableConfig', 'UserParameters',
    'ViewResultsTree', 'SummaryReport', 'AggregateGraph', 'AggregateReport', 'ResponseTimeGraph',
    'InfluxDBBackendListener', 'Summariser', 'GraphListener',
  ],
  ThreadGroup: [
    'HttpSampler', 'JDBCSampler', 'DebugSampler',
    'IfController', 'LoopController', 'WhileController', 'TransactionController',
    'ThroughputController', 'OnceOnlyController', 'ForEachController',
    'SwitchController', 'RandomController', 'InterleaveController',
    'IncludeController', 'ModuleController', 'RunTimeController',
    'CsvDataSource', 'HttpHeaderManager', 'HTTPCookieManager',
    'HTTPRequestDefaults', 'JDBCConnection', 'UserParameters',
    'ViewResultsTree', 'SummaryReport', 'AggregateGraph', 'AggregateReport',
    'ResponseTimeGraph', 'RandomVariableConfig', 'GraphListener',
  ],
  HttpSampler: [
    'ResponseAssertion', 'DurationAssertion', 'JSONPathAssertion',
    'BeanShellAssertion', 'JSR223Assertion', 'SizeAssertion',
    'XPathAssertion', 'CompareAssertion', 'XMLAssertion',
    'XPath2Assertion', 'HTMLAssertion', 'MD5HexAssertion', 'SMIMEAssertion',
    'RegexExtractor', 'JSONExtractor', 'BoundaryExtractor',
    'CSSSelectorExtractor', 'XPathExtractor',
    'ConstantTimer', 'UniformRandomTimer', 'GaussianRandomTimer',
    'SynchronizingTimer', 'ConstantThroughputTimer', 'PoissonRandomTimer',
    'BeanShellPreProcessor', 'BeanShellPostProcessor',
    'JSR223PreProcessor', 'JSR223PostProcessor',
    'UserParametersPreProcessor', 'SampleTimeout',
    'HttpHeaderManager', 'HTTPCookieManager',
  ],
  // 控制器统一可包含采样器和子控制器
  IfController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  LoopController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  WhileController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  TransactionController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  ThroughputController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  OnceOnlyController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  ForEachController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  SwitchController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  RandomController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  InterleaveController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  RunTimeController: ['HttpSampler', 'JDBCSampler', 'DebugSampler', 'IfController', 'LoopController', 'WhileController', 'TransactionController', 'ThroughputController', 'OnceOnlyController'],
  IncludeController: [],
  ModuleController: [],
  // 配置元素通常无子节点
  HttpHeaderManager: [],
  HTTPCookieManager: [],
  HttpCacheManager: [],
  HttpAuthManager: [],
  DNSCacheManager: [],
  HTTPRequestDefaults: [],
  CsvDataSource: [],
  RandomVariableConfig: [],
  UserParameters: [],
  JDBCConnection: [],
  // 监听器无子节点
  ViewResultsTree: [],
  SummaryReport: [],
  AggregateGraph: [],
  AggregateReport: [],
  ResponseTimeGraph: [],
  InfluxDBBackendListener: [],
  Summariser: [],
  GraphListener: [],
}

// 校验父子关系合法性(自动解析别名)
export const isValidParentChild = (parentType, childType) => {
  const resolvedParent = resolveType(parentType)
  const resolvedChild = resolveType(childType)
  const allowed = VALID_CHILDREN[resolvedParent]
  if (!allowed) return false
  // 同时支持规范名和别名(向后兼容)
  return allowed.includes(resolvedChild) || allowed.includes(childType)
}

// 节点分类(用于 UI 分组)
export const NODE_CATEGORIES = {
  container: '容器',
  sampler: '采样器',
  controller: '控制器',
  assertion: '断言',
  extractor: '提取器',
  timer: '定时器',
  preprocessor: '前置处理器',
  postprocessor: '后置处理器',
  config: '配置',
  listener: '监听器',
}
