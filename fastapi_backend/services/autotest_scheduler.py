"""
定时任务调度器模块（迁移自 auto_test_platform/services/scheduler.py）
使用 APScheduler 实现定时执行测试场景
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from fastapi_backend.core.config import settings
from fastapi_backend.services.autotest_report_service import write_allure_results

_logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"

scheduler: Optional[AsyncIOScheduler] = None

scheduled_tasks: Dict[str, Dict[str, Any]] = {}


def _schedule_meta_from_db(scenario_id: int, user_id: int = None) -> Dict[str, Any]:
    """从 PostgreSQL 读取定时配置（内存丢失或从 Job 重建时补全 Webhook 等）。"""
    import asyncio
    from fastapi_backend.core.database import async_session
    from fastapi_backend.models.autotest import AutoTestScenario
    from sqlalchemy import select

    async def _read() -> Dict[str, Any]:
        async with async_session() as session:
            query = select(
                AutoTestScenario.schedule_webhook_url,
                AutoTestScenario.schedule_cron_expression,
                AutoTestScenario.schedule_env_id,
                AutoTestScenario.schedule_task_name,
                AutoTestScenario.schedule_is_active,
            ).where(AutoTestScenario.id == scenario_id)
            if user_id is not None:
                query = query.where(AutoTestScenario.user_id == user_id)
            res = await session.execute(query)
            row = res.first()
            if not row:
                return {}
            return {
                "webhook_url": row[0],
                "cron_expression": row[1] or "",
                "env_id": row[2],
                "name": row[3],
                "is_active": True if row[4] is None else bool(row[4]),
            }

    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _read())
            return future.result(timeout=5)
    except RuntimeError:
        return asyncio.run(_read())
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
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            jobstore_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif db_url.startswith("postgresql://"):
            jobstore_url = db_url
        else:
            jobstore_url = f"sqlite:///{PROJECT_ROOT / 'instance' / 'scheduler_jobs.db'}"
        scheduler = AsyncIOScheduler(
            jobstores={'default': SQLAlchemyJobStore(url=jobstore_url)},
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300
            }
        )
    return scheduler


async def execute_scenario_job(scenario_id: int, env_id: Optional[int], task_id: str, user_id: int = None):
    """执行场景任务的异步函数 - 通过Celery发送任务"""
    import subprocess

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
                if task_id in scheduled_tasks:
                    scheduled_tasks[task_id]["status"] = "skipped"
                    scheduled_tasks[task_id]["last_error"] = "场景已停用，跳过执行"
                return
    except Exception as e:
        _logger.info(f"[Scheduler] 检查场景状态失败: {e}")

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
        max_wait_time = 300  # 5分钟超时
        wait_interval = 2    # 每2秒检查一次
        result = None

        try:
            for i in range(max_wait_time // wait_interval):
                try:
                    await asyncio.sleep(wait_interval)
                except asyncio.CancelledError:
                    _logger.info(f"[Scheduler] 任务 {task_id} 等待被取消，正在更新任务状态")
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
                raise TimeoutError(f"Celery任务超时: {celery_task_id}")
        except asyncio.CancelledError:
            _logger.info(f"[Scheduler] 任务 {task_id} 执行被完全取消")
            if task_id in scheduled_tasks:
                scheduled_tasks[task_id]["last_status"] = "cancelled"
                scheduled_tasks[task_id]["status"] = "idle"
            return  # 直接返回，不继续执行后续代码

        # 生成Allure报告
        allure_results_dir = AUTOTEST_DATA_DIR / "allure-results" / f"scenario_{scenario_id}"
        report_dir = AUTOTEST_DATA_DIR / "reports" / f"scenario_{scenario_id}"

        import shutil
        if allure_results_dir.exists():
            try:
                shutil.rmtree(str(allure_results_dir))
            except Exception as e:
                _logger.warning(f"清理 allure-results 目录失败: {e}")
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        history_id = str(uuid.uuid4())[:8]
        write_allure_results(allure_results_dir, scenario_id, result, history_id)

        try:
            import shutil
            old_report_history = report_dir / "history"
            new_results_history = allure_results_dir / "history"
            if old_report_history.exists() and old_report_history.is_dir():
                if new_results_history.exists():
                    shutil.rmtree(str(new_results_history))
                shutil.copytree(str(old_report_history), str(new_results_history))

            cmd_result = subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                timeout=60,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if cmd_result.returncode == 0:
                report_url = f"/reports/scenario_{scenario_id}/index.html"
            else:
                report_url = None
        except (FileNotFoundError, Exception):
            report_url = None

        if task_id in scheduled_tasks:
            if result:
                failed_steps = _failed_step_count(result)
                scheduled_tasks[task_id]["last_status"] = "success" if failed_steps == 0 else "failed"
                scheduled_tasks[task_id]["last_result"] = result
            else:
                scheduled_tasks[task_id]["last_status"] = "unknown"
                scheduled_tasks[task_id]["last_result"] = None
            scheduled_tasks[task_id]["report_url"] = report_url
            scheduled_tasks[task_id]["status"] = "idle"

            webhook_url = scheduled_tasks[task_id].get("webhook_url")
            if webhook_url:
                try:
                    import requests as _req
                    webhook_payload = {
                        "scenario_id": scenario_id,
                        "status": scheduled_tasks[task_id]["last_status"],
                        "report_url": report_url,
                        "total_steps": result.get("total_steps", 0) if result else 0,
                        "failed_steps": _failed_step_count(result),
                    }
                    await asyncio.to_thread(
                        _req.post, webhook_url, json=webhook_payload, timeout=10
                    )
                except Exception as wh_err:
                    _logger.warning(f"Webhook 通知失败 {webhook_url}: {wh_err}")

    except asyncio.CancelledError:
        _logger.info(f"[Scheduler] 任务 {task_id} 被取消执行")
        if task_id in scheduled_tasks:
            scheduled_tasks[task_id]["last_status"] = "cancelled"
            scheduled_tasks[task_id]["status"] = "idle"
    except Exception as e:
        _logger.info(f"[Scheduler] 任务 {task_id} 执行失败: {str(e)}")
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

    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError("Cron 表达式格式错误，应为 5 位：分 时 日 月 周")

    minute, hour, day, month, day_of_week = parts
    # 每场景固定一个 Job ID，便于持久化与前端展示，并用 replace_existing 更新同一调度
    task_id = f"auto_sched_{scenario_id}"

    job = get_scheduler().add_job(
        func=execute_scenario_job,
        trigger=CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
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

    scheduled_tasks[task_id] = task_info
    return task_info


def remove_scheduled_task(task_id: str) -> bool:
    """删除定时任务"""
    global scheduled_tasks
    try:
        sched = get_scheduler()
        sched.remove_job(task_id)
        if task_id in scheduled_tasks:
            del scheduled_tasks[task_id]
        return True
    except Exception as e:
        _logger.error(f"删除定时任务失败 {task_id}: {e}")
        return False


def toggle_task_status(task_id: str) -> Dict[str, Any]:
    """切换定时任务的启用/暂停状态"""
    global scheduled_tasks
    task_info = scheduled_tasks.get(task_id)
    if not task_info:
        raise ValueError(f"任务 {task_id} 不存在")

    is_active = task_info.get("is_active", True)
    sched = get_scheduler()

    _logger.info(f"[Scheduler] 切换任务状态: {task_id}, 当前is_active={is_active}, 调度器运行状态: {sched.running}")

    if is_active:
        # 暂停任务
        _logger.info(f"[Scheduler] 暂停任务: {task_id}")
        sched.pause_job(task_id)
        task_info["is_active"] = False
        task_info["status"] = "paused"
    else:
        # 恢复任务
        _logger.info(f"[Scheduler] 恢复任务: {task_id}")
        sched.resume_job(task_id)
        task_info["is_active"] = True
        task_info["status"] = "idle"

    # 验证作业状态
    job = sched.get_job(task_id)
    if job:
        _logger.info(f"[Scheduler] 作业状态: pending={job.pending}, next_run_time={job.next_run_time}")

    return {
        "task_id": task_id,
        "is_active": task_info["is_active"],
        "status": task_info["status"],
        "message": f"任务已{'启用' if task_info['is_active'] else '暂停'}"
    }


def get_scheduled_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务信息"""
    # 首先检查内存字典
    if task_id in scheduled_tasks:
        return scheduled_tasks.get(task_id)

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
        if hasattr(job.trigger, 'fields'):
            # CronTrigger
            fields = job.trigger.fields
            cron_expr = f"{fields[0]} {fields[1]} {fields[2]} {fields[3]} {fields[4]}"

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
            "is_active": not job.pending,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        }
        scheduled_tasks[task_id] = task_info
        return task_info

    return None


def get_all_scheduled_tasks(user_id: int = None) -> List[Dict[str, Any]]:
    """获取所有定时任务（可按用户过滤）"""
    sched = get_scheduler()

    # 首先确保scheduled_tasks包含所有调度器中的作业
    for job in sched.get_jobs():
        task_id = job.id
        if task_id not in scheduled_tasks:
            # 从作业重建任务信息
            args = job.args if job.args else []
            scenario_id = args[0] if len(args) > 0 else 0
            env_id = args[1] if len(args) > 1 else None
            job_user_id = args[3] if len(args) > 3 else None

            # 解析cron表达式
            cron_expr = ""
            if hasattr(job.trigger, 'fields'):
                # CronTrigger
                fields = job.trigger.fields
                cron_expr = f"{fields[0]} {fields[1]} {fields[2]} {fields[3]} {fields[4]}"

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
                "is_active": not job.pending,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
            scheduled_tasks[task_id] = task_info

    # 更新next_run_time；若内存中无 Webhook，从 DB 补全（避免仅内存字段丢失）
    for task_id, task_info in scheduled_tasks.items():
        try:
            job = sched.get_job(task_id)
            if job and job.next_run_time:
                task_info["next_run_time"] = job.next_run_time.isoformat()
            # 更新活动状态
            if job:
                task_info["is_active"] = not job.pending
        except Exception as e:
            _logger.warning(f"更新任务 next_run_time 失败 {task_id}: {e}")
        sid = task_info.get("scenario_id")
        if sid is not None and not (task_info.get("webhook_url") or "").strip():
            m = _schedule_meta_from_db(int(sid), user_id=task_info.get("user_id"))
            if m.get("webhook_url"):
                task_info["webhook_url"] = m.get("webhook_url")

    tasks = list(scheduled_tasks.values())
    if user_id is not None:
        tasks = [t for t in tasks if t.get("user_id") == user_id]
    return tasks


def get_tasks_by_scenario(scenario_id: int, user_id: int = None) -> List[Dict[str, Any]]:
    """获取指定场景的所有定时任务"""
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
