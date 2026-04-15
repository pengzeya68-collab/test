@echo off
cd /d C:\Users\lenovo\Desktop\TestMasterProject

echo ========================================
echo   Starting Celery Worker
echo ========================================
echo [1/1] Starting Celery worker...
set PYTHONIOENCODING=utf-8
start "TestMaster Celery Worker" cmd /k "py -3 -m celery -A fastapi_backend.tasks.celery_app worker --loglevel=info --pool=solo"
echo.
echo Celery worker started.
echo ========================================
pause