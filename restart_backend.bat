@echo off
cd /d %~dp0auto_test_platform
uvicorn main:app --reload --port 5002