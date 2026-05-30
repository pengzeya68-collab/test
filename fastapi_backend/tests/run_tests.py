"""
测试运行脚本（已废弃，不再作为主入口）

说明：
- 本项目测试已全面迁移到 pytest 体系。
- 请直接使用 pytest 运行测试，例如：
    pytest fastapi_backend/tests -q
    pytest fastapi_backend/tests/test_auth.py -q
- 保留此文件仅作为历史参考，不再维护 unittest 入口。
"""

import sys


def main():
    print("[WARN] run_tests.py 已废弃，请使用 pytest 直接运行测试。")
    print("示例：pytest fastapi_backend/tests -q")
    sys.exit(1)


if __name__ == "__main__":
    main()
