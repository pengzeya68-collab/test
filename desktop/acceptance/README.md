# TestMaster Desktop 验收测试

本目录是桌面端可复用验收入口。测试脚本的唯一实现保留在 `../scripts/`，由 `run.ps1` 和 `../scripts/run-business-acceptance.mjs` 统一调度，避免复制脚本后产生版本漂移。

## 运行前提

- 已构建的桌面包，例如 `../release-verified-27/win-unpacked/TestMaster Desktop.exe`。
- Node.js 可从命令行运行。
- 性能组需要本机 JMeter；默认路径为 `D:\Jmeter\apache-jmeter-5.1.1`。
- 每次运行使用独立的 `D:\TestMasterAcceptance\...` 数据目录，不使用真实用户数据。

## 常用命令

在项目根目录执行：

```powershell
.\desktop\acceptance\run.ps1 -Group exploratory
.\desktop\acceptance\run.ps1 -Group core
.\desktop\acceptance\run.ps1 -Group scenario
.\desktop\acceptance\run.ps1 -Group ui
.\desktop\acceptance\run.ps1 -Group platform
.\desktop\acceptance\run.ps1 -Group all
```

指定其他安装包：

```powershell
.\desktop\acceptance\run.ps1 -Group core -ReleasePath 'D:\Release\TestMaster Desktop.exe'
```

## 结果与准则

- 调度结果写入 `../test-artifacts/business-acceptance.json`。
- 每条脚本必须验证真实数据结果；页面可打开、出现预期错误提示不构成通过。
- 任意 `pageerror`、未断言的错误提示、5xx、卡死遮罩或脚本失败均视为验收失败。
- `suites.json` 是脚本职责与分组的台账；新增桌面功能时应先补充台账和对应验收脚本。

## 当前覆盖

- `core`：接口调试、脚本上传、环境、接口资产与场景创建。
- `scenario`：复杂编排、失败即停、定时、CI/CD、取消、套件与历史产物。
- `ui`：浏览器录制、手工 UI 用例、流量导入、数据工厂、登录态。
- `platform`：Mock、真实 JMeter、备份恢复、API 文档。
- `exploratory`：路由、错误反馈、重复操作、失效深链、AI 取消、桌面窄窗口布局。
