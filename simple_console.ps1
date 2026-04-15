# Simple TestMaster Service Console

$ProjectRoot = "C:\Users\lenovo\Desktop\TestMasterProject"

function Test-Port {
    param([int]$Port)
    $result = netstat -ano | Select-String ":$Port"
    return ($result | Select-String "LISTENING") -ne $null
}

function Test-Redis {
    $svc = Get-Service -Name Redis -ErrorAction SilentlyContinue
    return $svc -and $svc.Status -eq "Running"
}

function Show-Status {
    Write-Host ""
    Write-Host "=== Service Status ===" -ForegroundColor Cyan

    if (Test-Redis) {
        Write-Host "[Running] Redis" -ForegroundColor Green
    } else {
        Write-Host "[Stopped] Redis" -ForegroundColor Yellow
    }

    if (Test-Port 5001) {
        Write-Host "[Running] FastAPI (5001)" -ForegroundColor Green
    } else {
        Write-Host "[Stopped] FastAPI (5001)" -ForegroundColor Yellow
    }

    if (Test-Port 5173) {
        Write-Host "[Running] Frontend (5173)" -ForegroundColor Green
    } else {
        Write-Host "[Stopped] Frontend (5173)" -ForegroundColor Yellow
    }
    Write-Host ""
}

function Start-Redis {
    if (Test-Redis) {
        Write-Host "Redis already running" -ForegroundColor Yellow
        return
    }
    Write-Host "Starting Redis..." -ForegroundColor Cyan
    try {
        Start-Service -Name Redis -ErrorAction Stop
        Write-Host "Redis started" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start Redis: $_" -ForegroundColor Red
    }
}

function Stop-Redis {
    if (-not (Test-Redis)) {
        Write-Host "Redis not running" -ForegroundColor Yellow
        return
    }
    Write-Host "Stopping Redis..." -ForegroundColor Cyan
    try {
        Stop-Service -Name Redis -Force -ErrorAction Stop
        Write-Host "Redis stopped" -ForegroundColor Green
    } catch {
        Write-Host "Failed to stop Redis: $_" -ForegroundColor Red
    }
}

function Start-FastAPI {
    if (Test-Port 5001) {
        Write-Host "FastAPI already running on port 5001" -ForegroundColor Yellow
        return
    }
    Write-Host "Starting FastAPI..." -ForegroundColor Cyan
    $cmd = 'cd /d "' + $ProjectRoot + '" && set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 5001 --reload --reload-exclude "**/temp_pytest_tests/**" --reload-exclude "**/autotest_data/allure-results/**" --reload-exclude "**/autotest_data/reports/**" --reload-exclude "**/autotest_data/temp_run_data/**"'
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WorkingDirectory $ProjectRoot
    Write-Host "FastAPI started" -ForegroundColor Green
}

function Stop-FastAPI {
    if (-not (Test-Port 5001)) {
        Write-Host "FastAPI not running" -ForegroundColor Yellow
        return
    }
    Write-Host "Stopping FastAPI..." -ForegroundColor Cyan
    $lines = netstat -ano | Select-String ":5001" | Select-String "LISTENING"
    $pids = @()
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
        if ($parts.Count -ge 5) { $pids += $parts[-1] }
    }
    $pids = $pids | Select-Object -Unique
    foreach ($pid in $pids) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Write-Host "FastAPI stopped" -ForegroundColor Green
}

function Start-Frontend {
    if (Test-Port 5173) {
        Write-Host "Frontend already running on port 5173" -ForegroundColor Yellow
        return
    }
    Write-Host "Starting Frontend..." -ForegroundColor Cyan
    $cmd = "cd /d `"$ProjectRoot\frontend`" && npm run dev"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WorkingDirectory "$ProjectRoot\frontend"
    Write-Host "Frontend started" -ForegroundColor Green
}

function Stop-Frontend {
    if (-not (Test-Port 5173)) {
        Write-Host "Frontend not running" -ForegroundColor Yellow
        return
    }
    Write-Host "Stopping Frontend..." -ForegroundColor Cyan
    $lines = netstat -ano | Select-String ":5173" | Select-String "LISTENING"
    $pids = @()
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
        if ($parts.Count -ge 5) { $pids += $parts[-1] }
    }
    $pids = $pids | Select-Object -Unique
    foreach ($pid in $pids) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Frontend stopped" -ForegroundColor Green
}

function Start-All {
    Write-Host "Starting all services..." -ForegroundColor Cyan
    Start-Redis
    Start-Sleep -Seconds 2
    Start-FastAPI
    Start-Sleep -Seconds 2
    Start-Frontend
    Write-Host "All services started" -ForegroundColor Green
}

function Stop-All {
    Write-Host "Stopping all services..." -ForegroundColor Cyan
    Stop-Frontend
    Start-Sleep -Seconds 1
    Stop-FastAPI
    Start-Sleep -Seconds 1
    Stop-Redis
    Write-Host "All services stopped" -ForegroundColor Green
}

function Open-Url {
    param([string]$Url)
    Start-Process $Url
}

while ($true) {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TestMaster Service Console" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Project: $ProjectRoot"
    Show-Status

    Write-Host "=== Menu ===" -ForegroundColor Cyan
    Write-Host "1. Start all services"
    Write-Host "2. Stop all services"
    Write-Host "3. Refresh status"
    Write-Host ""
    Write-Host "4. Start Redis"
    Write-Host "5. Stop Redis"
    Write-Host "6. Start FastAPI"
    Write-Host "7. Stop FastAPI"
    Write-Host "8. Start Frontend"
    Write-Host "9. Stop Frontend"
    Write-Host ""
    Write-Host "10. Open Frontend (http://127.0.0.1:5173)"
    Write-Host "11. Open FastAPI Docs (http://127.0.0.1:5001/api/docs)"
    Write-Host ""
    Write-Host "0. Exit"
    Write-Host ""

    $choice = Read-Host "Enter choice"

    switch ($choice) {
        "1" { Start-All }
        "2" { Stop-All }
        "3" { }
        "4" { Start-Redis }
        "5" { Stop-Redis }
        "6" { Start-FastAPI }
        "7" { Stop-FastAPI }
        "8" { Start-Frontend }
        "9" { Stop-Frontend }
        "10" { Open-Url "http://127.0.0.1:5173" }
        "11" { Open-Url "http://127.0.0.1:5001/api/docs" }
        "0" { break }
        default { Write-Host "Invalid choice" -ForegroundColor Red }
    }

    if ($choice -ne "0") {
        Write-Host ""
        Write-Host "Press any key to continue..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

Write-Host "Console closed" -ForegroundColor Cyan