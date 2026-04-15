$ProjectRoot = "C:\Users\lenovo\Desktop\TestMasterProject"
$RedisUrl = "redis://localhost:6379/0"

function Test-PortListening {
    param([int]$Port)
    $result = netstat -ano | Select-String ":$Port"
    return ($result | Select-String "LISTENING") -ne $null
}

function Test-RedisRunning {
    $svc = Get-Service -Name Redis -ErrorAction SilentlyContinue
    return $svc -and $svc.Status -eq "Running"
}

function Show-Status {
    Write-Host ""
    if (Test-RedisRunning) {
        Write-Host "[运行中] Redis 服务" -ForegroundColor Green
    } else {
        Write-Host "[已停止] Redis 服务" -ForegroundColor Yellow
    }

    if (Test-PortListening 5001) {
        Write-Host "[运行中] FastAPI 后端 5001" -ForegroundColor Green
    } else {
        Write-Host "[已停止] FastAPI 后端 5001" -ForegroundColor Yellow
    }

    if (Test-PortListening 5173) {
        Write-Host "[运行中] 前端 Vite 5173" -ForegroundColor Green
    } else {
        Write-Host "[已停止] 前端 Vite 5173" -ForegroundColor Yellow
    }
}

function Start-RedisService {
    if (Test-RedisRunning) {
        Write-Host "Redis 已经在运行。" -ForegroundColor Yellow
        return
    }
    Write-Host "正在启动 Redis 服务..." -ForegroundColor Cyan
    try {
        Start-Service -Name Redis -ErrorAction Stop
        Write-Host "Redis 服务已启动。" -ForegroundColor Green
    } catch {
        Write-Host "无法启动 Redis 服务: $_" -ForegroundColor Red
        Write-Host "请确保 Redis 已安装为 Windows 服务。" -ForegroundColor Yellow
    }
}

function Stop-RedisService {
    $svc = Get-Service -Name Redis -ErrorAction SilentlyContinue
    if (-not $svc -or $svc.Status -ne "Running") {
        Write-Host "Redis 当前没有运行。" -ForegroundColor Yellow
        return
    }
    Stop-Service -Name Redis -Force
    Write-Host "Redis 已停止。" -ForegroundColor Cyan
}

function Start-FastAPIService {
    if (Test-PortListening 5001) {
        Write-Host "FastAPI 后端已经在运行，端口 5001 正在监听。" -ForegroundColor Yellow
        return
    }
    $cmd = 'cd /d "' + $ProjectRoot + '" && set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 5001 --reload --reload-exclude "**/temp_pytest_tests/**" --reload-exclude "**/autotest_data/allure-results/**" --reload-exclude "**/autotest_data/reports/**" --reload-exclude "**/autotest_data/temp_run_data/**"'
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WorkingDirectory $ProjectRoot
    Write-Host "已打开 FastAPI 后端窗口。" -ForegroundColor Cyan
}

function Stop-FastAPIService {
    $lines = netstat -ano | Select-String ":5001" | Select-String "LISTENING"
    if (-not $lines) {
        Write-Host "FastAPI 后端当前没有运行。" -ForegroundColor Yellow
        return
    }

    $pids = @()
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
        if ($parts.Count -ge 5) {
            $pids += $parts[-1]
        }
    }

    $pids = $pids | Select-Object -Unique
    foreach ($pid in $pids) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Write-Host "FastAPI 后端已停止。" -ForegroundColor Cyan
}

function Start-FrontendService {
    if (Test-PortListening 5173) {
        Write-Host "前端已经在运行，端口 5173 正在监听。" -ForegroundColor Yellow
        return
    }
    $cmd = 'cd /d "' + $ProjectRoot + '\frontend" && npm run dev'
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WorkingDirectory "$ProjectRoot\frontend"
    Write-Host "已打开前端窗口。" -ForegroundColor Cyan
}

function Stop-FrontendService {
    $lines = netstat -ano | Select-String ":5173" | Select-String "LISTENING"
    if (-not $lines) {
        Write-Host "前端当前没有运行。" -ForegroundColor Yellow
        return
    }

    $pids = @()
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
        if ($parts.Count -ge 5) {
            $pids += $parts[-1]
        }
    }

    $pids = $pids | Select-Object -Unique
    foreach ($pid in $pids) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Write-Host "前端已停止。" -ForegroundColor Cyan
}

function Start-AllServices {
    Start-RedisService
    Start-Sleep -Seconds 1
    Start-FastAPIService
    Start-Sleep -Seconds 1
    Start-FrontendService
}

function Stop-AllServices {
    Stop-FrontendService
    Stop-FastAPIService
    Stop-RedisService
}

function Open-Url {
    param([string]$Url)
    Start-Process $Url
}

while ($true) {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "TestMaster 服务控制台" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "项目目录: $ProjectRoot"
    Write-Host "Redis 地址: $RedisUrl"
    Show-Status
    Write-Host ""
    Write-Host "1. 启动全部服务"
    Write-Host "2. 停止全部服务"
    Write-Host "3. 刷新状态"
    Write-Host ""
    Write-Host "4. 启动 Redis"
    Write-Host "5. 停止 Redis"
    Write-Host "6. 启动 FastAPI 后端"
    Write-Host "7. 停止 FastAPI 后端"
    Write-Host "8. 启动前端"
    Write-Host "9. 停止前端"
    Write-Host ""
    Write-Host "10. 打开前端页面"
    Write-Host "11. 打开 FastAPI 文档"
    Write-Host ""
    Write-Host "0. 退出"
    Write-Host ""

    $choice = Read-Host "请输入编号"

    switch ($choice) {
        "1" { Start-AllServices }
        "2" { Stop-AllServices }
        "3" { }
        "4" { Start-RedisService }
        "5" { Stop-RedisService }
        "6" { Start-FastAPIService }
        "7" { Stop-FastAPIService }
        "8" { Start-FrontendService }
        "9" { Stop-FrontendService }
        "10" { Open-Url "http://127.0.0.1:5173" }
        "11" { Open-Url "http://127.0.0.1:5001/api/docs" }
        "0" { break }
        default { Write-Host "输入无效，请重新选择。" -ForegroundColor Red }
    }

    if ($choice -ne "0") {
        Write-Host ""
        Pause
    }
}