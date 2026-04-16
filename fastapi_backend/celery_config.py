"""
Celery configuration for TestMaster FastAPI project.
从 config.py 读取 broker 和 result_backend 配置，支持 .env 环境变量覆盖
"""
import os
from celery import Celery

app = Celery('testmaster')

broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

app.conf.timezone = 'Asia/Shanghai'

app.conf.task_routes = {
    'fastapi_backend.tasks.run_scenario': {'queue': 'celery'},
    'fastapi_backend.tasks.run_case': {'queue': 'celery'},
    'fastapi_backend.tasks.send_email': {'queue': 'celery'},
}

app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60
app.conf.task_soft_time_limit = 25 * 60
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100

app.autodiscover_tasks(['fastapi_backend.tasks'])
