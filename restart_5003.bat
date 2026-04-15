@echo off
cd /d C:\Users\lenovo\Desktop\TestMasterProject
echo Port 5003 standalone mode has been retired.
echo Restarting the unified FastAPI backend on port 5001 instead...
start /B set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --reload --reload-exclude "**/temp_pytest_tests/**" --reload-exclude "**/autotest_data/allure-results/**" --reload-exclude "**/autotest_data/reports/**" --reload-exclude "**/autotest_data/temp_run_data/**" --port 5001 --host 0.0.0.0
