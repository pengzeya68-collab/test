@echo off
chcp 65001 >nul
echo ==========================================
echo TestMaster 后端测试脚本
echo ==========================================
echo.

cd /d %~dp0

echo [1/2] 运行指定测试文件...
pytest fastapi_backend/tests/test_auth.py fastapi_backend/tests/test_sandbox.py fastapi_backend/tests/test_ai_evaluation.py fastapi_backend/tests/test_interview_session.py fastapi_backend/tests/test_submission.py -q

echo.
echo [2/2] 运行全部测试...
pytest fastapi_backend/tests -q

echo.
echo ==========================================
echo 测试完成
echo ==========================================
pause
