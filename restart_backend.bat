@echo off
cd /d C:\Users\lenovo\Desktop\TestMasterProject
echo Restart script now targets the unified FastAPI backend.
set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --reload --reload-exclude "**/temp_pytest_tests/**" --reload-exclude "**/autotest_data/allure-results/**" --reload-exclude "**/autotest_data/reports/**" --reload-exclude "**/autotest_data/temp_run_data/**" --port 5001 --host 0.0.0.0
