"""
Celery configuration for TestMaster FastAPI project.
从 config.py 的 settings 对象读取 broker 和 result_backend 配置
"""

import logging

from celery import Celery

from fastapi_backend.core.config import settings

_logger = logging.getLogger(__name__)

app = Celery("testmaster")

broker_url = settings.CELERY_BROKER_URL or settings.REDIS_URL or ""
result_backend = settings.CELERY_RESULT_BACKEND or ""

# 若未配置 Redis，则降级为 SQLite 模式（仅本地开发/测试可用，不用于生产）
if not broker_url:
    broker_url = "sqlalchemy+sqlite:///celery_broker.db"
    _logger.warning("CELERY_BROKER_URL 未配置，Celery 降级为 SQLite 模式（仅本地开发/测试）")
else:
    _logger.info("Celery broker 已配置: %s", broker_url.split("@")[-1] if "@" in broker_url else broker_url)

if not result_backend:
    result_backend = "db+sqlite:///celery_results.db"
    _logger.warning("CELERY_RESULT_BACKEND 未配置，Celery 结果后端降级为 SQLite 模式（仅本地开发/测试）")
else:
    _logger.info("Celery result_backend 已配置: %s", result_backend.split("@")[-1] if "@" in result_backend else result_backend)

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]

app.conf.timezone = "Asia/Shanghai"
app.conf.enable_utc = True

app.conf.task_routes = {
    "fastapi_backend.tasks.run_scenario": {"queue": "celery"},
    "fastapi_backend.tasks.send_email": {"queue": "celery"},
    "fastapi_backend.services.autotest_ai_generator.ai_generate_task": {"queue": "celery"},
    # JMeter 真实引擎压测任务，独立队列避免阻塞常规 Celery 任务
    "fastapi_backend.tasks.run_jmeter_bench": {"queue": "jmeter"},
}

app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60
app.conf.task_soft_time_limit = 25 * 60
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100

# Redis 健康检查（防止 broker 连接断开后不重连）
app.conf.broker_connection_retry_on_startup = True

# 关键: 必须在 worker 启动时显式 import 所有 model,
# 否则 JmeterBenchRun.user_id 等外键引用 "users.id" 时会抛 NoReferencedTableError
import fastapi_backend.models.models  # noqa: F401
import fastapi_backend.models.autotest  # noqa: F401
import fastapi_backend.models.autotest_jmeter_models  # noqa: F401

# Celery worker 启动钩子(每个 ForkPoolWorker 子进程初始化时执行)
from celery.signals import worker_process_init

@worker_process_init.connect
def _setup_metadata(**kwargs):
    """每个 ForkPoolWorker 子进程初始化时,确保所有 model 都已注册到 Base.metadata。
    父进程正确 import 不代表 fork 后的子进程也注册了(子进程继承父进程内存,
    但 ORM class 的 __table__ 引用若发生在子进程的某次延迟导入,
    可能找不到 users 表)。这里显式 import 一次,确保万无一失。
    """
    import logging as _lg
    _lg.getLogger(__name__).info(
        "[worker_process_init] re-importing models for child pid=%d",
        __import__("os").getpid(),
    )
    import fastapi_backend.models.models  # noqa: F401
    import fastapi_backend.models.autotest  # noqa: F401
    import fastapi_backend.models.autotest_jmeter_models  # noqa: F401
    from fastapi_backend.core.database import Base
    _lg.getLogger(__name__).info(
        "[worker_process_init] metadata tables=%d, has users=%s",
        len(Base.metadata.tables),
        "users" in Base.metadata.tables,
    )

app.autodiscover_tasks(["fastapi_backend.tasks"])
