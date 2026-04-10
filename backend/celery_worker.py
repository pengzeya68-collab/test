# -*- coding: utf-8 -*-
"""
Celery 异步任务配置
Flask + Celery + Redis 异步任务队列架构

启动 Worker：
    celery -A backend.celery_worker worker --loglevel=info -P solo

Windows 兼容模式使用 -P solo（不支持 Windows 的 prefork）
"""

from celery import Celery
import os

# Redis 作为消息中间件（broker）和结果后端（backend）
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# 创建 Celery 实例
celery_app = Celery(
    'testmaster',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.celery_tasks']
)

# Celery 配置
celery_app.conf.update(
    # 任务结果过期时间（秒）
    result_expires=3600,
    # 任务序列化方式
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    # 时区
    timezone='Asia/Shanghai',
    enable_utc=True,
    # 任务追踪
    task_track_started=True,
    # 任务结果自动保存到 backend
    result_extended=True,
    # 单进程 + Windows 兼容模式
    worker_pool='solo',
    # 任务超时（秒）
    task_soft_time_limit=600,
    task_time_limit=900,
    # 避免重复执行（相同参数的任务如果还在执行中则不重复）
    task_ignore_duplicate=True,
)