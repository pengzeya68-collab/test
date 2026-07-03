@echo off
chcp 65001 >nul
echo ========================================
echo   TestMaster 一键部署到服务器
echo ========================================
echo.

REM 请通过环境变量或修改此文件设置服务器信息
set SERVER_IP=%SERVER_IP%
if "%SERVER_IP%"=="" (
    echo 错误: 请设置 SERVER_IP 环境变量，或修改此文件
    pause
    exit /b 1
)
set SERVER_USER=root
set SERVER_PATH=/root/TestMaster

echo [1/5] 构建前端...
cd /d "%~dp0frontend"
set VITE_FASTAPI_BASE_URL=https://%SERVER_IP%
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
ssh -o StrictHostKeyChecking=accept-new %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && git pull"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 服务器拉取代码失败！
    pause
    exit /b 1
)
echo ✅ 代码已同步

echo.
echo [4/5] 重启 Docker 服务...
ssh -o StrictHostKeyChecking=accept-new %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && docker compose up -d --build"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker 启动失败！
    pause
    exit /b 1
)
echo ✅ 服务已重启

echo.
echo [5/5] 检查服务状态...
ssh -o StrictHostKeyChecking=accept-new %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && sleep 5 && docker compose ps && curl -s http://localhost:5001/api/health"
echo.

echo [6/5] 修复静态文件权限（nginx worker 为 www-data）...
ssh -o StrictHostKeyChecking=accept-new %SERVER_USER%@%SERVER_IP% "chmod -R o+rX /opt/testmaster/frontend/dist 2>/dev/null && echo '✅ 权限已修复'"
echo.

echo ========================================
echo   🎉 部署完成！
echo.
echo   前端页面: https://%SERVER_IP%
echo   API接口:  https://%SERVER_IP%/api/health
echo ========================================
pause
