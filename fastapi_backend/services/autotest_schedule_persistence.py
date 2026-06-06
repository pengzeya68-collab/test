"""Persist AutoTest scheduler settings on test_scenarios so reload/restart keeps cron + webhook."""
from __future__ import annotations

from typing import Any, Optional
import logging

from sqlalchemy import select, text
from fastapi_backend.core.autotest_database import async_session
from fastapi_backend.models.autotest import AutoTestScenario

_logger = logging.getLogger(__name__)


async def ensure_schedule_columns_on_db() -> None:
    """Ensure schedule columns exist on test_scenarios (PostgreSQL compatible)."""
    async with async_session() as session:
        def _migrate(sync_conn: Any) -> None:
            r = sync_conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'test_scenarios'"
            ))
            existing = {row[0] for row in r.fetchall()}
            for col, ddl in _schedule_column_ddl():
                if col not in existing:
                    sync_conn.execute(text(ddl))

        await session.run_sync(_migrate)
        await session.commit()


def _schedule_column_ddl() -> list[tuple[str, str]]:
    return [
        ("schedule_cron_expression", "ALTER TABLE test_scenarios ADD COLUMN schedule_cron_expression VARCHAR(200)"),
        ("schedule_env_id", "ALTER TABLE test_scenarios ADD COLUMN schedule_env_id INTEGER"),
        ("schedule_webhook_url", "ALTER TABLE test_scenarios ADD COLUMN schedule_webhook_url TEXT"),
        ("schedule_task_name", "ALTER TABLE test_scenarios ADD COLUMN schedule_task_name VARCHAR(200)"),
        ("schedule_is_active", "ALTER TABLE test_scenarios ADD COLUMN schedule_is_active BOOLEAN DEFAULT TRUE"),
    ]


async def persist_schedule_to_db(
    scenario_id: int,
    cron_expression: str,
    env_id: Optional[int],
    webhook_url: Optional[str],
    name: Optional[str],
    is_active: bool,
    user_id: int = None,
) -> None:
    async with async_session() as session:
        query = select(AutoTestScenario).where(AutoTestScenario.id == scenario_id)
        if user_id is not None:
            query = query.where(AutoTestScenario.user_id == user_id)
        res = await session.execute(query)
        row = res.scalar_one_or_none()
        if not row:
            return
        row.schedule_cron_expression = cron_expression
        row.schedule_env_id = env_id
        row.schedule_webhook_url = webhook_url or None
        row.schedule_task_name = name
        row.schedule_is_active = is_active
        await session.commit()


async def persist_schedule_is_active_db(scenario_id: int, is_active: bool, user_id: int = None) -> None:
    async with async_session() as session:
        query = select(AutoTestScenario).where(AutoTestScenario.id == scenario_id)
        if user_id is not None:
            query = query.where(AutoTestScenario.user_id == user_id)
        res = await session.execute(query)
        row = res.scalar_one_or_none()
        if not row:
            return
        row.schedule_is_active = is_active
        await session.commit()


async def clear_schedule_from_db(scenario_id: int, user_id: int = None) -> None:
    async with async_session() as session:
        query = select(AutoTestScenario).where(AutoTestScenario.id == scenario_id)
        if user_id is not None:
            query = query.where(AutoTestScenario.user_id == user_id)
        res = await session.execute(query)
        row = res.scalar_one_or_none()
        if not row:
            return
        row.schedule_cron_expression = None
        row.schedule_env_id = None
        row.schedule_webhook_url = None
        row.schedule_task_name = None
        row.schedule_is_active = False  # 清除调度时应设为 False，避免重启时恢复空 cron 的任务
        await session.commit()


async def load_scenarios_with_schedule() -> list[AutoTestScenario]:
    async with async_session() as session:
        res = await session.execute(
            select(AutoTestScenario).where(
                AutoTestScenario.schedule_cron_expression.isnot(None),
                AutoTestScenario.schedule_cron_expression != "",
            )
        )
        return list(res.scalars().all())


async def restore_scheduler_jobs_from_db() -> None:
    """应用启动时从 DB 恢复 APScheduler 任务。"""
    from fastapi_backend.services.autotest_scheduler import add_scheduled_task

    scenarios = await load_scenarios_with_schedule()
    for s in scenarios:
        cron = (s.schedule_cron_expression or "").strip()
        if not cron:
            continue
        # 注意：不根据 s.is_active 跳过——场景停用但调度启用时仍应恢复调度，
        # execute_scenario_job 运行时会检查 is_active 并跳过执行
        if s.schedule_is_active is False:
            # 调度被暂停，恢复任务但保持暂停状态
            try:
                add_scheduled_task(
                    scenario_id=s.id,
                    cron_expression=cron,
                    env_id=s.schedule_env_id,
                    webhook_url=s.schedule_webhook_url,
                    task_name=s.schedule_task_name,
                    is_active=False,
                    user_id=s.user_id,
                )
            except Exception as e:
                _logger.error(f"[Scheduler] 从数据库恢复暂停任务失败 scenario_id={s.id}: {e}")
            continue
        try:
            add_scheduled_task(
                scenario_id=s.id,
                cron_expression=cron,
                env_id=s.schedule_env_id,
                webhook_url=s.schedule_webhook_url,
                task_name=s.schedule_task_name,
                is_active=s.schedule_is_active if s.schedule_is_active is not None else True,
                user_id=s.user_id,
            )
        except Exception as e:
            _logger.error(f"[Scheduler] 从数据库恢复任务失败 scenario_id={s.id}: {e}")


def read_schedule_webhook_sync(scenario_id: int, user_id: int = None) -> Optional[str]:
    """同步读取场景的定时 Webhook（供 Celery worker 等非 async 上下文使用）。"""
    import asyncio

    async def _read() -> Optional[str]:
        async with async_session() as session:
            query = select(AutoTestScenario.schedule_webhook_url).where(AutoTestScenario.id == scenario_id)
            if user_id is not None:
                query = query.where(AutoTestScenario.user_id == user_id)
            res = await session.execute(query)
            row = res.scalar_one_or_none()
            if not row:
                return None
            # scalar_one_or_none 返回标量值，但防御性处理 Row 对象
            val = row[0] if hasattr(row, '__getitem__') and not isinstance(row, str) else row
            if val is None:
                return None
            s = str(val).strip()
            return s or None

    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _read())
            return future.result(timeout=5)
    except RuntimeError:
        return asyncio.run(_read())
    except Exception as e:
        _logger.warning(f"读取定时任务 webhook URL 失败: {e}")
        return None
