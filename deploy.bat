@echo off
chcp 65001 >nul
echo ========================================
echo   TestMaster 一键部署到服务器
echo ========================================
echo.

set SERVER_IP=34.150.26.84
set SERVER_USER=root
set SERVER_PATH=/root/TestMaster

echo [1/5] 构建前端...
cd /d "%~dp0frontend"
set VITE_FASTAPI_BASE_URL=http://%SERVER_IP%:5001
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 前端构建失败！
    pause
    exit /b 1
)
echo ✅ 前端构建完成

echo.
echo [2/5] 提交代码到 GitHub...
cd /d "%~dp0"
git add -A
git commit -m "deploy: 自动部署更新 %date% %time%" 2>nul
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Git 推送可能失败，继续尝试部署...
)
echo ✅ 代码已推送

echo.
echo [3/5] 连接服务器拉取最新代码...
ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && git pull"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 服务器拉取代码失败！
    pause
    exit /b 1
)
echo ✅ 代码已同步

echo.
echo [4/5] 重启 Docker 服务...
ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && docker compose up -d --build"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker 启动失败！
    pause
    exit /b 1
)
echo ✅ 服务已重启

echo.
echo [5/5] 检查服务状态...
ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && sleep 5 && docker compose ps && curl -s http://localhost:5001/api/health"
echo.

echo ========================================
echo   🎉 部署完成！
echo.
echo   前端页面: http://%SERVER_IP%
echo   API接口:  http://%SERVER_IP%:5001/api/health
echo ========================================
pause
