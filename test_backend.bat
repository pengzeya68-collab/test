@echo off
chcp 65001 > nul
echo ========================================
echo     Flask 后端启动诊断
echo ========================================
echo.

cd /d "c:\Users\lenovo\Desktop\TestMasterProject"
echo [1] 检查 Python...
python --version
echo.

echo [2] 检查依赖...
python -c "import flask; print('  Flask:', flask.__version__)"
python -c "import flask_sqlalchemy; print('  Flask-SQLAlchemy: OK')"
python -c "import flask_jwt_extended; print('  Flask-JWT-Extended: OK')"
echo.

echo [3] 测试后端导入...
python -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.app import create_app
    print('  [OK] backend.app 导入成功')
    app = create_app()
    print('  [OK] App 创建成功')
except Exception as e:
    print('  [ERROR]', e)
    import traceback
    traceback.print_exc()
"
echo.

echo [4] 尝试启动后端 (5秒测试)...
timeout /t 5 /nobreak > nul & python backend/app.py &

echo.
echo ========================================
echo     诊断完成
echo ========================================
pause
