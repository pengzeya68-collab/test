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

## 公网真实项目验收

本验收将公网 TestMaster 视为被测系统，并由桌面安装包完成登录、接口调试、项目隔离、接口场景、真实网页登录 UI 用例，以及真实接口流量的脱敏、转换和失败预览门禁。它会创建独立账号和项目数据，并验证可删除资产能被清理；若服务端报告项目删除 blocker，验收必须失败，不能把残留数据当作成功。不要把它与默认的本地隔离验收混用。

```powershell
$env:PRODUCTION_BASE_URL = 'http://35.194.164.151'
$env:TESTMASTER_PACKAGED_EXE = 'D:\TestMasterReleases\release-public-acceptance-29\win-unpacked\TestMaster Desktop.exe'
$env:TESTMASTER_PRODUCTION_DESKTOP_DATA_DIR = 'D:\TestMasterAcceptance\production-desktop-real-project'
Push-Location .\desktop
node .\scripts\test-production-desktop-e2e.mjs
Pop-Location
```

通过标准为输出 JSON 的 `passed: true`，并且包含 `public-login-page-browser-run`、`desktop-capture-to-assets` 与 `redacted-capture-preview-gate` 三项。失败现场会保存到 `D:\TestMasterAcceptance\production-desktop-artifacts`。

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
