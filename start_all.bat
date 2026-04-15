@echo off
cd /d C:\Users\lenovo\Desktop\TestMasterProject

echo ========================================
echo   Starting TestMaster Unified Backend
echo ========================================
echo [1/1] Starting FastAPI unified backend on port 5001...
start "TestMaster Unified Backend (5001)" cmd /k "set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 5001 --reload --reload-exclude ""**/temp_pytest_tests/**"" --reload-exclude ""**/autotest_data/allure-results/**"" --reload-exclude ""**/autotest_data/reports/**"" --reload-exclude ""**/autotest_data/temp_run_data/**"""
echo.
echo Unified backend: http://localhost:5001
echo API docs       : http://localhost:5001/api/docs
echo Notes          : Unified backend: native FastAPI only, legacy bridges disabled
echo ========================================
pause
