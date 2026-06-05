"""
Celery configuration for TestMaster FastAPI project.
从 config.py 读取 broker 和 result_backend 配置，支持 .env 环境变量覆盖
"""
import os
import logging

from celery import Celery

_logger = logging.getLogger(__name__)

app = Celery('testmaster')

broker_url = os.environ.get('CELERY_BROKER_URL', '')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', '')

# 若未配置 Redis，则降级为 SQLite 模式（仅本地开发/测试可用，不用于生产）
if not broker_url:
    broker_url = 'sqlalchemy+sqlite:///celery_broker.db'
    _logger.warning("CELERY_BROKER_URL 未配置，Celery 降级为 SQLite 模式（仅本地开发/测试）")
if not result_backend:
    result_backend = 'db+sqlite:///celery_results.db'
    _logger.warning("CELERY_RESULT_BACKEND 未配置，Celery 结果后端降级为 SQLite 模式（仅本地开发/测试）")

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

app.conf.timezone = 'Asia/Shanghai'

app.conf.task_routes = {
    'fastapi_backend.tasks.run_scenario': {'queue': 'celery'},
    'fastapi_backend.tasks.send_email': {'queue': 'celery'},
    'fastapi_backend.services.autotest_ai_generator.ai_generate_task': {'queue': 'celery'},
}

app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60
app.conf.task_soft_time_limit = 25 * 60
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100

app.autodiscover_tasks(['fastapi_backend.tasks'])
