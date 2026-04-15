#!/usr/bin/env python3
"""
检查调度器状态
"""
import sys
sys.path.insert(0, '.')

from fastapi_backend.services.autotest_scheduler import get_scheduler, get_all_scheduled_tasks

sched = get_scheduler()
print("调度器运行状态:", sched.running)
print("调度器作业数量:", len(sched.get_jobs()))
print("调度器作业列表:")
for job in sched.get_jobs():
    print(f"  - ID: {job.id}, 名称: {job.name}, 下次运行时间: {job.next_run_time}, 触发器: {job.trigger}")

print("\n所有定时任务:")
tasks = get_all_scheduled_tasks()
for task in tasks:
    print(f"  - 任务ID: {task['task_id']}, 场景ID: {task['scenario_id']}, cron: {task['cron_expression']}, 是否激活: {task['is_active']}")