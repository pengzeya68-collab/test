@echo off
chcp 65001 > nul
echo ========================================
echo   Unified FastAPI Backend Diagnostic
echo ========================================
echo.

cd /d "C:\Users\lenovo\Desktop\TestMasterProject"
echo [1] Checking Python...
python --version
echo.

echo [2] Checking unified backend import...
python -c "
import sys
sys.path.insert(0, '.')
try:
    from fastapi_backend.main import app
    print('  [OK] fastapi_backend.main imported successfully')
    print('  [OK] App title:', app.title)
except Exception as e:
    print('  [ERROR]', e)
    import traceback
    traceback.print_exc()
"
echo.

echo [3] Checking unified service syntax...
py -3 -m py_compile fastapi_backend\main.py
echo.

echo ========================================
echo   Diagnostic complete
echo ========================================
pause
