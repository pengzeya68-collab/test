@echo off
cd /d c:\Users\lenovo\Desktop\TestMasterProject
echo Starting Flask backend on port 5000...
start "Flask Backend" cmd /k "python -m backend.app"
timeout /t 3 /nobreak >nul
echo Flask should be running on port 5000