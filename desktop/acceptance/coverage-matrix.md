# 桌面端验收覆盖矩阵

本台账只记录可复跑、可核验的证据。`页面可加载`不等于功能通过；每个功能至少需要一条真实数据闭环和一条关键失败/恢复路径。

## 判定口径

- **P（页面）**：路由、标题、基础布局、控制台/5xx/卡死遮罩检查。
- **B（业务）**：通过界面真实创建、编辑、执行、查看结果和清理数据；同时验证持久化 API 状态。
- **E（异常）**：必填校验、非法输入、重复提交、取消、超时/失败、重试或恢复。
- **I（隔离/联动）**：项目隔离、上下游资产引用、执行状态机或跨模块数据传递。

未列出 B/E/I 证据的功能不得作为发布验收通过。

| 功能入口 | P | B/E/I 验收脚本 | 当前状态 | 补充验收重点 |
|---|---|---|---|---|
| 工作概览 | `test-exploratory-route-sweep` | `test-exploratory-route-sweep` | 已有基础 | 服务状态、快捷入口、失败反馈 |
| 项目工作区 | 无 | `test-workspace-project-isolation-e2e` | 已覆盖核心闭环 | 新建/校验/切换、元素资产跨项目隔离、切换后自动刷新；成员与服务故障待补 |
| 接口调试 | `route-sweep` | `test-api-debugger-e2e` | 已覆盖 | 请求、保存、脚本、异常响应 |
| 接口用例 | `route-sweep` | `test-interface-assets-scenarios-e2e` | 已覆盖 | 增删改、场景引用、变量解析 |
| 业务场景/编辑器 | `route-sweep` | `test-scenario-*.mjs` | 已覆盖 | 长链路、失败策略、取消、数据驱动、历史 |
| 接口回归套件 | `route-sweep` | `test-suite-e2e` | 已覆盖 | 执行、取消、状态与结果 |
| 数据工厂 | `route-sweep` | `test-data-factory-e2e` | 已覆盖 | 数据生成、绑定与异常 |
| 流量导入/工作台 | 部分 | `test-traffic-*-e2e` | 已覆盖 | 捕获、脱敏、导入、转换、失败回退 |
| 通知中心 | 无 | `test-notification-center-e2e` | 已覆盖核心闭环 | 渠道类型、校验、密钥保留、测试投递失败、删除；执行触发和重试状态待补 |
| Mock 服务 | `route-sweep` | `test-mock-service-e2e` | 已覆盖 | 命中、故障、日志、回退 |
| 备份恢复 | `route-sweep` | `test-backup-manager-e2e` | 已覆盖 | 导出、恢复、冲突与清理 |
| UI 用例/编辑/套件 | 部分 | `test-ui-manual-authoring-e2e`、`test-recorder*.mjs` | 已覆盖 | 录制、编辑、运行、登录态、失败产物 |
| 元素仓库 | 无 | `test-ui-governance-e2e` | 待补 | 页面对象、定位器策略、编辑、项目隔离、绑定 |
| Flaky 检测 | 无 | `test-ui-governance-e2e` | 待补 | 真实历史归类、筛选、隔离/解除隔离 |
| 视觉回归 | 无 | `test-visual-regression-e2e` | 待补 | 基线、对比、掩码、阈值、审核、资源失败 |
| 缺陷中心 | 无 | `test-ui-governance-e2e` | 待补 | Tracker、失败建缺陷、状态筛选、失败反馈 |
| Trace Viewer | 无 | `test-ui-governance-e2e` | 待补 | 列表、详情、动作/截图资源、资源缺失 |
| 自愈历史 | 无 | `test-ui-governance-e2e` | 待补 | 建议、批准/拒绝、关联资产变更 |
| 网络拦截 | 无 | `test-ui-governance-e2e` | 待补 | 创建、编辑、删除、分配、规则生效 |
| 契约测试 | 无 | `test-contract-health-protocol-e2e` | 待补 | 快照、Diff、规则、合法/非法响应校验 |
| API 健康 | 无 | `test-contract-health-protocol-e2e` | 待补 | 创建、即时检查、成功/失败阈值、历史 |
| 评审与覆盖 | 无 | `test-review-flow-shard-e2e` | 待补 | 评审、意见、通过/打回、需求关联、覆盖率 |
| 流程编排 | 无 | `test-review-flow-shard-e2e` | 待补 | 节点/边保存、非法连线、刷新后还原 |
| 分片进度 | 无 | `test-review-flow-shard-e2e` | 待补 | 创建分片、进度、失败分片与重试展示 |
| 协议调试 | 无 | `test-contract-health-protocol-e2e` | 待补 | WebSocket/SSE/gRPC 参数校验、连接失败、结果展示 |
| JMeter | `route-sweep` | `test-jmeter-e2e` | 已覆盖 | 真正执行、报告、错误处理 |
| AI 用例生成 | `route-sweep` | `test-ai-tools-coverage-e2e` | 待补 | 空输入、取消、服务失败、结果导入 |
| 覆盖率 | `route-sweep` | `test-ai-tools-coverage-e2e` | 待补 | 真实资产下统计、空态、筛选 |
| API 文档/预览 | `route-sweep` | `test-api-doc-preview-e2e` | 已覆盖 | 生成、预览与错误路径 |
| 工具箱 | `route-sweep` | `test-ai-tools-coverage-e2e` | 待补 | 每个可交互工具、格式错误和复制/导出 |

## 统一异常门禁

所有 E2E 脚本必须监听并失败于下列未声明情况：

1. `pageerror`、未断言 console error、HTTP 5xx、请求意外中止。
2. 操作完成后仍存在的 loading mask、禁用状态未恢复、意外弹窗。
3. 误报成功但 API 未持久化，或 API 成功而 UI 未刷新。
4. 重复点击造成的重复记录、跨项目可见、刷新后数据丢失。
5. 取消/删除后残留的引用、轮询任务和临时数据。

## 代码分支原则

不宣称代码 100% 分支覆盖。浏览器内核、操作系统、第三方 SDK 和不可达兜底分支需要标注豁免原因；所有业务状态机、用户输入校验、数据隔离、失败恢复、幂等与关键 API 分支必须由单元/集成/E2E 三层至少一层覆盖，并在报告里保留命令和结果。
