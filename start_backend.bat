@echo off
cd /d C:\Users\lenovo\Desktop\TestMasterProject
set PYTHONIOENCODING=utf-8 && py -3 -m uvicorn fastapi_backend.main:app --port 5001 --host 0.0.0.0 --no-reload
