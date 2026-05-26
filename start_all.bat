@echo off
chcp 65001 >nul
echo ==========================================
echo TestMaster 一键启动脚本
echo ==========================================
echo.
echo 本脚本将依次启动：
echo   1. FastAPI 后端（端口 5001）
echo   2. Vue 3 主前端（端口 5173）
echo.
echo 如需单独启动，请使用：
echo   start_backend.bat   - 仅启动后端
echo   start_frontend.bat  - 仅启动主前端
echo   start_workspace.bat - 仅启动辅助前端
echo ==========================================
echo.

REM 启动后端
echo [1/2] 启动 FastAPI 后端...
start "TestMaster Backend" cmd /k "cd /d %~dp0fastapi_backend && python -m uvicorn main:app --host 0.0.0.0 --port 5001 --reload"
timeout /t 3 /nobreak >nul

REM 启动前端
echo [2/2] 启动 Vue 3 主前端...
start "TestMaster Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ==========================================
echo 启动完成！
echo 后端地址：http://localhost:5001
echo 前端地址：http://localhost:5173
echo ==========================================
pause
