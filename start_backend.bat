@echo off
setlocal
cd /d %~dp0

set "CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,null"

echo [TestMaster] Starting backend on http://127.0.0.1:5001

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn fastapi_backend.main:app --host 127.0.0.1 --port 5001
) else (
    py -3 -m uvicorn fastapi_backend.main:app --host 127.0.0.1 --port 5001
)

if errorlevel 1 (
    echo.
    echo [TestMaster] Backend failed to start.
    pause
)
