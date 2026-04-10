$ErrorActionPreference = "Continue"
$projectRoot = "c:/Users/lenovo/Desktop/TestMasterProject"

$env:PYTHONPATH = $projectRoot

# Kill processes on ports 5000, 5002, 5173
$ports = @(5000, 5002, 5173)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 3

# 1. Flask on 5000
$flaskProc = Start-Process -FilePath "py" -ArgumentList "-3", "auto_test_platform/run_flask.py" -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
Write-Host "Flask started: PID=$($flaskProc.Id)"

Start-Sleep -Seconds 3

# 2. FastAPI on 5002 (使用 -NoProfile 避免加载用户配置，-Environment 显式传递环境变量)
$fastapiProc = Start-Process -FilePath "py" -ArgumentList "-3", "-m", "uvicorn", "auto_test_platform.main:app", "--port", "5002", "--host", "127.0.0.1" -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -Environment @{"PYTHONPATH"=$projectRoot}
Write-Host "FastAPI started: PID=$($fastapiProc.Id)"

Start-Sleep -Seconds 3

# 3. Vite on 5173
$viteProc = Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "$projectRoot/frontend" -WindowStyle Hidden -PassThru
Write-Host "Vite started: PID=$($viteProc.Id)"

Start-Sleep -Seconds 3

# Verify
Write-Host ""
Write-Host "=== Port Status ==="
Get-NetTCPConnection -LocalPort 5000,5002,5173 -ErrorAction SilentlyContinue | Format-Table LocalAddress,LocalPort,State,OwningProcess -AutoSize
