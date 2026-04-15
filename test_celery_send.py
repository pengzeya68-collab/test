#!/usr/bin/env python3
"""
测试Celery任务发送
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi_backend.tasks import task_run_scenario

if __name__ == "__main__":
    print("测试发送Celery任务...")
    try:
        task = task_run_scenario.delay(1, None)  # scenario_id=1, env_id=None
        print(f"任务发送成功，任务ID: {task.id}")
        print(f"任务状态: {task.status}")
    except Exception as e:
        print(f"任务发送失败: {e}")
        import traceback
        traceback.print_exc()