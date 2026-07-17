$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$unpackedApp = Join-Path $projectRoot 'desktop\release\win-unpacked\TestMaster Desktop.exe'
$portableApp = Join-Path $projectRoot 'desktop\release\TestMaster Desktop-1.0.0-portable.exe'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$healthUrl = 'http://127.0.0.1:5001/api/ui-automation/health'
$logDir = Join-Path $projectRoot 'logs'
$stdoutLog = Join-Path $logDir 'desktop-backend.log'
$stderrLog = Join-Path $logDir 'desktop-backend-error.log'

Add-Type -AssemblyName PresentationFramework
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Show-LaunchError([string]$message) {
    [System.Windows.MessageBox]::Show($message, 'TestMaster 启动失败', 'OK', 'Error') | Out-Null
}

function Test-Backend {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
        return $health.status -eq 'ok' -and $health.enabled -eq $true -and $health.module -eq 'ui-automation'
    } catch {
        return $false
    }
}

$appPath = if (Test-Path -LiteralPath $unpackedApp) { $unpackedApp } elseif (Test-Path -LiteralPath $portableApp) { $portableApp } else { $null }
if (-not $appPath) {
    Show-LaunchError "未找到 TestMaster Desktop 1.0.0。请确认 desktop\release 目录完整。"
    exit 1
}

if (-not (Test-Backend)) {
    if (-not (Test-Path -LiteralPath $python)) {
        Show-LaunchError "本机后端环境不完整：缺少 .venv\Scripts\python.exe。请先完成部署，或在登录页配置企业 TestMaster 服务地址。"
        exit 1
    }
    Remove-Item -LiteralPath $stdoutLog,$stderrLog -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','fastapi_backend.main:app','--host','127.0.0.1','--port','5001') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog | Out-Null
    $deadline = (Get-Date).AddSeconds(45)
    do {
        Start-Sleep -Milliseconds 500
        $ready = Test-Backend
    } while (-not $ready -and (Get-Date) -lt $deadline)
    if (-not $ready) {
        Show-LaunchError "后台服务启动失败。请查看：$stderrLog"
        exit 1
    }
}

Start-Process -FilePath $appPath -WorkingDirectory (Split-Path -Parent $appPath)

