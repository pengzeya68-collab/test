import sys
sys.path.insert(0, '.')

try:
    from fastapi_backend.services.autotest_scheduler import get_scheduler
    print("导入成功")
except Exception as e:
    print(f"导入失败: {e}")
    import traceback
    traceback.print_exc()