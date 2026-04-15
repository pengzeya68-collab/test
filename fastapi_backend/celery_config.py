"""
Celery configuration for TestMaster FastAPI project.
"""
from celery import Celery

# 创建Celery应用
app = Celery('testmaster')

# Redis作为broker和结果后端
app.conf.broker_url = 'redis://127.0.0.1:6379/0'
app.conf.result_backend = 'redis://127.0.0.1:6379/0'

# 任务序列化设置
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# 时区设置
app.conf.timezone = 'Asia/Shanghai'

# 任务路由
app.conf.task_routes = {
    'fastapi_backend.tasks.run_scenario': {'queue': 'celery'},
    'fastapi_backend.tasks.run_case': {'queue': 'celery'},
    'fastapi_backend.tasks.send_email': {'queue': 'celery'},
}

# 任务执行设置
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30分钟
app.conf.task_soft_time_limit = 25 * 60  # 25分钟
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100

# 自动发现任务
app.autodiscover_tasks(['fastapi_backend.tasks'])