"""
定时任务调度器模块（迁移自 auto_test_platform/services/scheduler.py）
使用 APScheduler 实现定时执行测试场景
"""

import asyncio
import copy
import logging
import threading
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.base import JobLookupError

from fastapi_backend.core.config import settings

_logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"

scheduler: Optional[AsyncIOScheduler] = None
_scheduler_lock = threading.Lock()

# 注意：scheduled_tasks是进程内字典，多Worker部署时需配合分布式锁使用
scheduled_tasks: Dict[str, Dict[str, Any]] = {}
_scheduled_tasks_lock = threading.Lock()


def _schedule_meta_from_db(scenario_id: int, user_id: int = None) -> Dict[str, Any]:
    """从 PostgreSQL 读取定时配置（内存丢失或从 Job 重建时补全 Webhook 等）。

    使用同步 psycopg2 连接，避免在同步上下文中跨事件循环使用 async_session 导致
    'Task got Future attached to a different loop' 错误。
    """
    import re
    from fastapi_backend.core.config import settings

    # 将 asyncpg URL 转为 psycopg2 格式
    db_url = settings.DATABASE_URL
    sync_url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", db_url)

    try:
        if sync_url.startswith(("sqlite:///", "sqlite+aiosqlite:///")):
            import sqlite3

            sqlite_path = re.sub(r"^sqlite(?:\+aiosqlite)?:///", "", sync_url)
            conn = sqlite3.connect(sqlite_path, timeout=5)
            placeholder = "?"
        else:
            import psycopg2

            conn = psycopg2.connect(sync_url, connect_timeout=5)
            conn.autocommit = True
            placeholder = "%s"
        cur = conn.cursor()
        if user_id is not None:
            cur.execute(
                "SELECT schedule_webhook_url, schedule_cron_expression, "
                "schedule_env_id, schedule_task_name, schedule_is_active "
                f"FROM test_scenarios WHERE id = {placeholder} AND user_id = {placeholder}",
                (scenario_id, user_id),
            )
        else:
            cur.execute(
                "SELECT schedule_webhook_url, schedule_cron_expression, "
                "schedule_env_id, schedule_task_name, schedule_is_active "
                f"FROM test_scenarios WHERE id = {placeholder}",
                (scenario_id,),
            )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return {}
        return {
            "webhook_url": row[0],
            "cron_expression": row[1] or "",
            "env_id": row[2],
            "name": row[3],
            "is_active": True if row[4] is None else bool(row[4]),
        }
    except Exception as e:
        _logger.warning(f"读取定时配置失败: {e}")
        return {}


def _failed_step_count(result: Optional[dict]) -> int:
    if not result:
        return 0
    v = result.get("failed_steps")
    if v is not None:
        return int(v)
    v2 = result.get("failed_count")
    if v2 is not None:
        return int(v2)
    return 0


def get_scheduler() -> AsyncIOScheduler:
    """获取全局调度器实例"""
    global scheduler
    if scheduler is None:
        with _scheduler_lock:
            if scheduler is None:
                db_url = settings.DATABASE_URL
                if db_url.startswith("postgresql+asyncpg://"):
                    jobstore_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
                elif db_url.startswith("postgresql://"):
                    jobstore_url = db_url
                else:
                    data_root = Path(os.getenv("TESTMASTER_DATA_DIR", str(PROJECT_ROOT / "instance")))
                    data_root.mkdir(parents=True, exist_ok=True)
                    jobstore_url = f"sqlite:///{data_root / 'scheduler_jobs.db'}"
                scheduler = AsyncIOScheduler(
                    jobstores={"default": SQLAlchemyJobStore(url=jobstore_url)},
                    job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 300},
                )
    return scheduler


async def execute_scenario_job(scenario_id: int, env_id: Optional[int], task_id: str, user_id: int = None):
    """执行场景任务的异步函数 - 通过Celery发送任务"""

    _logger.info(f"[Scheduler] 开始执行任务 {task_id}, 场景 {scenario_id}")

    try:
        from fastapi_backend.core.autotest_database import AsyncSessionLocal
        from fastapi_backend.models.autotest import AutoTestScenario
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            query = select(AutoTestScenario).where(AutoTestScenario.id == scenario_id)
            if user_id is not None:
                query = query.where(AutoTestScenario.user_id == user_id)
            result = await db.execute(query)
            scenario = result.scalar_one_or_none()
            if not scenario or not scenario.is_active:
                _logger.info(f"[Scheduler] 场景 {scenario_id} 已停用或不存在，跳过执行")
                with _scheduled_tasks_lock:
                    if task_id in scheduled_tasks:
                        scheduled_tasks[task_id]["status"] = "skipped"
                        scheduled_tasks[task_id]["last_error"] = "场景已停用，跳过执行"
                return
    except Exception as e:
        _logger.info(f"[Scheduler] 检查场景状态失败: {e}")

    with _scheduled_tasks_lock:
        if task_id in scheduled_tasks:
            scheduled_tasks[task_id]["last_run"] = datetime.now(timezone.utc).isoformat()
            scheduled_tasks[task_id]["status"] = "running"

    try:
        # 通过Celery发送任务
        from fastapi_backend.tasks import task_run_scenario

        # 创建Celery任务
        _logger.info(f"[Scheduler] 发送Celery任务: scenario_id={scenario_id}, env_id={env_id}")
        celery_task = task_run_scenario.delay(scenario_id, env_id, user_id)

        if not celery_task:
            raise ValueError("Celery任务创建失败，task为None")

        celery_task_id = celery_task.id
        if not celery_task_id:
            raise ValueError("Celery任务ID为空，任务可能未成功发送")

        _logger.info(f"[Scheduler] Celery任务已发送，任务ID: {celery_task_id}")

        # 等待任务完成（异步等待）
        # 注意：APScheduler线程中阻塞轮询会占用调度器线程池，超时设为30秒，
        # 超时后记录警告并让任务在后台继续执行，不阻塞调度器线程
        max_wait_time = 30  # 30秒超时（原5分钟会长时间阻塞调度器线程池）
        wait_interval = 2  # 每2秒检查一次
        result = None

        try:
            for i in range(max_wait_time // wait_interval):
                try:
                    await asyncio.sleep(wait_interval)
                except asyncio.CancelledError:
                    _logger.info(f"[Scheduler] 任务 {task_id} 等待被取消，正在更新任务状态")
                    with _scheduled_tasks_lock:
                        if task_id in scheduled_tasks:
                            scheduled_tasks[task_id]["last_status"] = "cancelled"
                            scheduled_tasks[task_id]["status"] = "idle"
                    raise  # 重新抛出，让外层处理

                # 检查任务状态
                from celery.result import AsyncResult
                from fastapi_backend.tasks import app as celery_app

                task_result = AsyncResult(celery_task_id, app=celery_app)

                if task_result.ready():
                    if task_result.successful():
                        result = task_result.result
                        _logger.info(f"[Scheduler] Celery任务完成: {celery_task_id}")
                        break
                    else:
                        error_msg = str(task_result.result) if task_result.result else "任务执行失败"
                        raise Exception(f"Celery任务执行失败: {error_msg}")
            else:
                # 超时：不阻塞调度器线程，记录警告并让任务在后台继续执行
                _logger.warning(
                    f"[Scheduler] Celery任务 {celery_task_id} 等待 {max_wait_time}秒 未完成，"
                    f"放行后台执行，任务 {task_id} 状态置为 running_in_background"
                )
                with _scheduled_tasks_lock:
                    if task_id in scheduled_tasks:
                        scheduled_tasks[task_id]["last_status"] = "running_in_background"
                        scheduled_tasks[task_id]["status"] = "idle"
                return  # 不继续执行后续结果处理逻辑，任务在后台继续
        except asyncio.CancelledError:
            _logger.info(f"[Scheduler] 任务 {task_id} 执行被完全取消")
            with _scheduled_tasks_lock:
                if task_id in scheduled_tasks:
                    scheduled_tasks[task_id]["last_status"] = "cancelled"
                    scheduled_tasks[task_id]["status"] = "idle"
            return  # 直接返回，不继续执行后续代码

        # Webhook和Allure报告由tasks.py和scenario_runner处理，调度器不再重复生成
        # - Webhook 通知：由 tasks.py 的 notify_scenario_schedule_webhook_from_db 统一发送
        # - Allure 报告：由 scenario_runner 在执行过程中生成
        with _scheduled_tasks_lock:
            if task_id in scheduled_tasks:
                if result:
                    failed_steps = _failed_step_count(result)
                    scheduled_tasks[task_id]["last_status"] = "success" if failed_steps == 0 else "failed"
                    # 仅存储摘要信息，避免内存膨胀
                    scheduled_tasks[task_id]["last_result"] = {
                        "total_steps": result.get("total_steps", 0),
                        "failed_steps": failed_steps,
                        "success_steps": result.get("success_steps", 0),
                    }
                else:
                    scheduled_tasks[task_id]["last_status"] = "unknown"
                    scheduled_tasks[task_id]["last_result"] = None
                scheduled_tasks[task_id]["status"] = "idle"

    except asyncio.CancelledError:
        _logger.info(f"[Scheduler] 任务 {task_id} 被取消执行")
        with _scheduled_tasks_lock:
            if task_id in scheduled_tasks:
                scheduled_tasks[task_id]["last_status"] = "cancelled"
                scheduled_tasks[task_id]["status"] = "idle"
    except Exception as e:
        _logger.info(f"[Scheduler] 任务 {task_id} 执行失败: {str(e)}")
        with _scheduled_tasks_lock:
            if task_id in scheduled_tasks:
                scheduled_tasks[task_id]["last_status"] = "error"
                scheduled_tasks[task_id]["last_error"] = str(e)
                scheduled_tasks[task_id]["status"] = "idle"


def add_scheduled_task(
    scenario_id: int,
    cron_expression: str,
    env_id: Optional[int] = None,
    webhook_url: Optional[str] = None,
    task_name: Optional[str] = None,
    is_active: Optional[bool] = True,
    user_id: int = None,
) -> Dict[str, Any]:
    """添加定时任务"""
    global scheduled_tasks

    # 多Worker部署防护：以DB中schedule_is_active为准，避免重复调度或恢复已停用任务
    try:
        meta = _schedule_meta_from_db(scenario_id, user_id=user_id)
        db_is_active = meta.get("is_active")
        if db_is_active is False and is_active is not False:
            _logger.info(f"[Scheduler] DB显示场景 {scenario_id} 调度已停用，按DB状态添加为暂停")
            is_active = False
    except Exception as e:
        _logger.warning(f"[Scheduler] 读取DB调度状态失败 {scenario_id}: {e}")

    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError("Cron 表达式格式错误，应为 5 位：分 时 日 月 周")

    minute, hour, day, month, day_of_week = parts
    # 每场景固定一个 Job ID，便于持久化与前端展示，并用 replace_existing 更新同一调度
    task_id = f"auto_sched_{scenario_id}"

    job = get_scheduler().add_job(
        func=execute_scenario_job,
        trigger=CronTrigger(
            minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, timezone=ZoneInfo("Asia/Shanghai")
        ),
        args=[scenario_id, env_id, task_id, user_id],
        id=task_id,
        name=task_name or f"场景 {scenario_id} 定时执行",
        replace_existing=True,
    )

    # 根据is_active参数设置作业状态
    sched = get_scheduler()
    if is_active is False:
        sched.pause_job(task_id)

    task_info = {
        "task_id": task_id,
        "job_id": job.id,
        "scenario_id": scenario_id,
        "env_id": env_id,
        "cron_expression": cron_expression,
        "webhook_url": webhook_url,
        "name": task_name or f"场景 {scenario_id} 定时执行",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_run": None,
        "last_status": None,
        "last_error": None,
        "last_result": None,
        "report_url": None,
        "status": "idle",
        "is_active": is_active if is_active is not None else True,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "user_id": user_id,
    }

    with _scheduled_tasks_lock:
        scheduled_tasks[task_id] = task_info
    return task_info


def _scenario_id_from_task_id(task_id: str) -> Optional[int]:
    """从task_id解析scenario_id（格式: auto_sched_{scenario_id}）"""
    prefix = "auto_sched_"
    if task_id.startswith(prefix):
        try:
            return int(task_id[len(prefix) :])
        except ValueError:
            return None
    return None


def _clear_schedule_status_in_db(task_id: str) -> None:
    """同步清空DB中场景的schedule_is_active状态（供remove_scheduled_task调用）。

    使用同步 psycopg2 连接，避免在同步调度器上下文中嵌套事件循环。
    """
    import re
    import psycopg2
    from fastapi_backend.core.config import settings

    scenario_id = _scenario_id_from_task_id(task_id)
    if scenario_id is None:
        return

    db_url = settings.DATABASE_URL
    sync_url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", db_url)

    try:
        conn = psycopg2.connect(sync_url, connect_timeout=5)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "UPDATE test_scenarios SET schedule_is_active = false WHERE id = %s",
            (scenario_id,),
        )
        cur.close()
        conn.close()
    except Exception as e:
        _logger.warning(f"清空DB调度状态失败 {task_id}: {e}")


def remove_scheduled_task(task_id: str) -> bool:
    """删除定时任务"""
    global scheduled_tasks
    try:
        sched = get_scheduler()
        try:
            sched.remove_job(task_id)
        except JobLookupError:
            # Idempotent cleanup: a stale DB/cache entry must still be removable.
            pass
        with _scheduled_tasks_lock:
            if task_id in scheduled_tasks:
                del scheduled_tasks[task_id]
        return True
    except Exception as e:
        _logger.error(f"删除定时任务失败 {task_id}: {e}")
        return False


def toggle_task_status(task_id: str) -> Dict[str, Any]:
    """切换定时任务的启用/暂停状态（使用乐观锁避免TOCTOU竞态）"""
    global scheduled_tasks
    from fastapi import HTTPException

    sched = get_scheduler()

    # 读取调用方预期的当前状态（代表调用方基于该状态发起切换）
    with _scheduled_tasks_lock:
        task_info = scheduled_tasks.get(task_id)
        if not task_info:
            raise ValueError(f"任务 {task_id} 不存在")
        current_is_active = task_info.get("is_active", True)

    new_is_active = not current_is_active

    _logger.info(
        f"[Scheduler] 切换任务状态: {task_id}, 当前is_active={current_is_active}, "
        f"目标is_active={new_is_active}, 调度器运行状态: {sched.running}"
    )

    # 原子更新：使用乐观锁，仅在状态未被并发请求修改时才写入
    with _scheduled_tasks_lock:
        task_info = scheduled_tasks.get(task_id)
        if not task_info:
            raise ValueError(f"任务 {task_id} 不存在")
        # 乐观锁校验：当前值必须与调用方读取的预期值一致
        if task_info.get("is_active", True) != current_is_active:
            raise HTTPException(status_code=409, detail="任务状态已被其他请求修改，请重试")
        task_info["is_active"] = new_is_active
        task_info["status"] = "idle" if new_is_active else "paused"

    # 锁外操作调度器（APScheduler 自身线程安全，避免长时间持锁）
    try:
        if new_is_active:
            _logger.info(f"[Scheduler] 恢复任务: {task_id}")
            sched.resume_job(task_id)
        else:
            _logger.info(f"[Scheduler] 暂停任务: {task_id}")
            sched.pause_job(task_id)
    except Exception:
        # Keep the in-memory cache aligned when APScheduler rejects the change.
        with _scheduled_tasks_lock:
            task_info = scheduled_tasks.get(task_id)
            if task_info:
                task_info["is_active"] = current_is_active
                task_info["status"] = "idle" if current_is_active else "paused"
        raise

    # 验证作业状态
    job = sched.get_job(task_id)
    if job:
        _logger.info(f"[Scheduler] 作业状态: pending={job.pending}, next_run_time={job.next_run_time}")

    with _scheduled_tasks_lock:
        return {
            "task_id": task_id,
            "is_active": task_info["is_active"],
            "status": task_info["status"],
            "message": f"任务已{'启用' if task_info['is_active'] else '暂停'}",
        }


def get_scheduled_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务信息"""
    # 首先检查内存字典
    with _scheduled_tasks_lock:
        if task_id in scheduled_tasks:
            return copy.deepcopy(scheduled_tasks.get(task_id))

    # 如果内存中没有，检查调度器中是否有此任务
    sched = get_scheduler()
    job = sched.get_job(task_id)
    if job:
        # 从作业重建基本任务信息
        args = job.args if job.args else []
        scenario_id = args[0] if len(args) > 0 else 0
        env_id = args[1] if len(args) > 1 else None
        job_user_id = args[3] if len(args) > 3 else None

        # 解析cron表达式
        cron_expr = ""
        meta = _schedule_meta_from_db(scenario_id, user_id=job_user_id)
        task_info = {
            "task_id": task_id,
            "job_id": job.id,
            "scenario_id": scenario_id,
            "env_id": env_id if env_id is not None else meta.get("env_id"),
            "cron_expression": cron_expr or meta.get("cron_expression") or "",
            "webhook_url": meta.get("webhook_url"),
            "name": (meta.get("name") or job.name or f"场景 {scenario_id} 定时执行"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run": None,
            "last_status": None,
            "last_error": None,
            "last_result": None,
            "report_url": None,
            "status": "idle",
            "is_active": job.next_run_time is not None,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "user_id": job_user_id,
        }
        with _scheduled_tasks_lock:
            scheduled_tasks[task_id] = task_info
        return copy.deepcopy(task_info)


def get_all_scheduled_tasks(user_id: int = None) -> List[Dict[str, Any]]:
    """获取所有定时任务（可按用户过滤）"""
    sched = get_scheduler()

    # 首先确保scheduled_tasks包含所有调度器中的作业
    for job in sched.get_jobs():
        task_id = job.id
        with _scheduled_tasks_lock:
            already_loaded = task_id in scheduled_tasks
        if not already_loaded:
            # 从作业重建任务信息
            args = job.args if job.args else []
            scenario_id = args[0] if len(args) > 0 else 0
            env_id = args[1] if len(args) > 1 else None
            job_user_id = args[3] if len(args) > 3 else None

            # 解析cron表达式
            cron_expr = ""
            meta = _schedule_meta_from_db(scenario_id, user_id=job_user_id)
            task_info = {
                "task_id": task_id,
                "job_id": job.id,
                "scenario_id": scenario_id,
                "env_id": env_id if env_id is not None else meta.get("env_id"),
                "cron_expression": cron_expr or meta.get("cron_expression") or "",
                "webhook_url": meta.get("webhook_url"),
                "name": (meta.get("name") or job.name or f"场景 {scenario_id} 定时执行"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_run": None,
                "last_status": None,
                "last_error": None,
                "last_result": None,
                "report_url": None,
                "status": "idle",
                "is_active": job.next_run_time is not None,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "user_id": job_user_id,
            }
            with _scheduled_tasks_lock:
                scheduled_tasks[task_id] = task_info

    # 更新next_run_time；若内存中无 Webhook，从 DB 补全
    with _scheduled_tasks_lock:
        task_ids = list(scheduled_tasks.keys())
    for task_id in task_ids:
        with _scheduled_tasks_lock:
            task_info = scheduled_tasks.get(task_id)
        if not task_info:
            continue
        try:
            job = sched.get_job(task_id)
            if job and job.next_run_time:
                task_info["next_run_time"] = job.next_run_time.isoformat()
            # 更新活动状态
            if job:
                task_info["is_active"] = job.next_run_time is not None
        except Exception as e:
            _logger.warning(f"更新任务 next_run_time 失败 {task_id}: {e}")
        sid = task_info.get("scenario_id")
        if sid is not None and not (task_info.get("webhook_url") or "").strip():
            m = _schedule_meta_from_db(int(sid), user_id=task_info.get("user_id"))
            if m.get("webhook_url"):
                task_info["webhook_url"] = m.get("webhook_url")

    with _scheduled_tasks_lock:
        tasks = list(scheduled_tasks.values())
    if user_id is not None:
        tasks = [t for t in tasks if t.get("user_id") == user_id]
    return tasks


def get_tasks_by_scenario(scenario_id: int, user_id: int = None) -> List[Dict[str, Any]]:
    """获取指定场景的所有定时任务"""
    with _scheduled_tasks_lock:
        tasks = [task for task in scheduled_tasks.values() if task["scenario_id"] == scenario_id]
    if user_id is not None:
        tasks = [t for t in tasks if t.get("user_id") == user_id]
    return tasks


def start_scheduler():
    """启动调度器"""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        _logger.info("[Scheduler] 调度器已启动")


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        _logger.info("[Scheduler] 调度器已停止")
    scheduler = None
