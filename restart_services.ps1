$ErrorActionPreference = "Continue"
$projectRoot = "c:/Users/lenovo/Desktop/TestMasterProject"

$env:PYTHONPATH = $projectRoot

# Kill processes on ports 5001, 5173
$ports = @(5001, 5173)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 3

# 1. Unified FastAPI backend on 5001
$fastapiProc = Start-Process -FilePath "py" -ArgumentList "-3", "-m", "uvicorn", "fastapi_backend.main:app", "--port", "5001", "--host", "0.0.0.0", "--reload", "--reload-exclude", "**/temp_pytest_tests/**", "--reload-exclude", "**/autotest_data/allure-results/**", "--reload-exclude", "**/autotest_data/reports/**", "--reload-exclude", "**/autotest_data/temp_run_data/**" -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -Environment @{"PYTHONPATH"=$projectRoot; "PYTHONIOENCODING"="utf-8"}
Write-Host "Unified FastAPI backend started: PID=$($fastapiProc.Id)"

Start-Sleep -Seconds 3

# 3. Vite on 5173
$viteProc = Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "$projectRoot/frontend" -WindowStyle Hidden -PassThru
Write-Host "Vite started: PID=$($viteProc.Id)"

Start-Sleep -Seconds 3

# Verify
Write-Host ""
Write-Host "=== Port Status ==="
Get-NetTCPConnection -LocalPort 5001,5173 -ErrorAction SilentlyContinue | Format-Table LocalAddress,LocalPort,State,OwningProcess -AutoSize
