param(
  [ValidateSet('core', 'scenario', 'ui', 'platform', 'exploratory', 'all')]
  [string]$Group = 'all',
  [string]$ReleasePath = 'D:\TestMasterReleases\release-verified-28\win-unpacked\TestMaster Desktop.exe',
  [string]$JmeterHome = 'D:\Jmeter\apache-jmeter-5.1.1'
)

$desktopRoot = Split-Path -Parent $PSScriptRoot
$manifest = Get-Content (Join-Path $PSScriptRoot 'suites.json') -Raw | ConvertFrom-Json
$resolvedRelease = [IO.Path]::GetFullPath($ReleasePath)
if (-not (Test-Path -LiteralPath $resolvedRelease)) { throw "未找到桌面安装包: $resolvedRelease" }

$scripts = if ($Group -eq 'all') {
  @($manifest.groups.PSObject.Properties | ForEach-Object { $_.Value } | Select-Object -Unique)
} else {
  @($manifest.groups.$Group)
}
if (-not $scripts.Count) { throw "未找到测试组: $Group" }

$env:TESTMASTER_PACKAGED_EXE = $resolvedRelease
$env:TESTMASTER_ACCEPTANCE_DATA_DIR = 'D:\TestMasterAcceptance\runs\current'
$env:TESTMASTER_ACCEPTANCE_ONLY = $scripts -join ','
$env:JMETER_ENGINE_ENABLED = 'true'
$env:JMETER_HOME = $JmeterHome
$env:JMETER_BIN = Join-Path $JmeterHome 'bin\jmeter.bat'

Write-Host "测试组: $Group"
Write-Host "安装包: $resolvedRelease"
Write-Host "隔离数据: $env:TESTMASTER_ACCEPTANCE_DATA_DIR"
Push-Location $desktopRoot
try { node scripts\run-business-acceptance.mjs } finally { Pop-Location }
