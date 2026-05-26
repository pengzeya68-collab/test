@echo off
chcp 65001 >nul
echo ========================================
echo   TestMaster 快速部署（仅后端代码）
echo ========================================
echo.

set SERVER_IP=34.150.26.84
set SERVER_USER=root
set SERVER_PATH=/root/TestMaster

echo [1/3] 推送代码到 GitHub...
cd /d "%~dp0"
git add -A
git commit -m "deploy: 后端更新 %date% %time%" 2>nul
git push origin main
echo ✅ 代码已推送

echo.
echo [2/3] 服务器拉取并重建...
ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && git pull && docker compose up -d --build backend celery-worker"
echo ✅ 后端已更新

echo.
echo [3/3] 检查状态...
ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && sleep 5 && docker compose ps && curl -s http://localhost:5001/api/health"
echo.
echo 🎉 后端部署完成！
pause
