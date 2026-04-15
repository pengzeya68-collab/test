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

    foreach ($item in @(
        @{ Port = 5001; Name = "FastAPI 后端 5001" },
        @{ Port = 5173; Name = "前端 Vite 5173" }
    )) {
        if (Test-PortListening $item.Port) {
            Write-Host "[运行中] $($item.Name)" -ForegroundColor Green
        } else {
            Write-Host "[已停止] $($item.Name)" -ForegroundColor Yellow
        }
    }
}

function Start-RedisService {
    if (Test-RedisRunning) {
        Write-Host "Redis 已经在运行。" -ForegroundColor Yellow
        return
    }
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "`"$ProjectRoot\codex_start_redis.bat`"" -WorkingDirectory $ProjectRoot
    Write-Host "已打开 Redis 启动窗口。" -ForegroundColor Cyan
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


function Start-PortService {
    param(
        [int]$Port,
        [string]$Name,
        [string]$ScriptName
    )
    if (Test-PortListening $Port) {
        Write-Host "$Name 已经在运行，端口 $Port 正在监听。" -ForegroundColor Yellow
        return
    }

    # 根据端口启动不同的服务
    if ($Port -eq 5001) {
        # FastAPI后端
        $cmd = 'cd /d "' + $ProjectRoot + '" && set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 5001 --reload --reload-exclude "**/temp_pytest_tests/**" --reload-exclude "**/autotest_data/allure-results/**" --reload-exclude "**/autotest_data/reports/**" --reload-exclude "**/autotest_data/temp_run_data/**"'
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WorkingDirectory $ProjectRoot
        Write-Host "已打开 FastAPI 后端窗口。" -ForegroundColor Cyan
    } elseif ($Port -eq 5173) {
        # 前端服务
        $cmd = 'cd /d "' + $ProjectRoot + '\frontend" && npm run dev'
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WorkingDirectory "$ProjectRoot\frontend"
        Write-Host "已打开前端窗口。" -ForegroundColor Cyan
    } else {
        Write-Host "不支持端口 $Port 的服务。" -ForegroundColor Red
    }
}

function Stop-PortService {
    param(
        [int]$Port,
        [string]$Name
    )
    $lines = netstat -ano | Select-String ":$Port" | Select-String "LISTENING"
    if (-not $lines) {
        Write-Host "$Name 当前没有运行。" -ForegroundColor Yellow
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
    Write-Host "$Name 已停止。" -ForegroundColor Cyan
}

function Start-AllServices {
    Start-RedisService
    Start-Sleep -Seconds 2
    Start-PortService -Port 5001 -Name "FastAPI 后端" -ScriptName ""
    Start-Sleep -Seconds 2
    Start-PortService -Port 5173 -Name "前端 Vite" -ScriptName ""
}

function Stop-AllServices {
    Stop-PortService -Port 5173 -Name "前端 Vite"
    Stop-PortService -Port 5001 -Name "FastAPI 后端"
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
        "6" { Start-PortService -Port 5001 -Name "FastAPI 后端" -ScriptName "" }
        "7" { Stop-PortService -Port 5001 -Name "FastAPI 后端" }
        "8" { Start-PortService -Port 5173 -Name "前端 Vite" -ScriptName "" }
        "9" { Stop-PortService -Port 5173 -Name "前端 Vite" }
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
