"""Persist AutoTest scheduler settings on test_scenarios so reload/restart keeps cron + webhook."""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select, text
from fastapi_backend.core.autotest_database import async_session
from fastapi_backend.models.autotest import AutoTestScenario


def _schedule_column_ddl() -> list[tuple[str, str]]:
    return [
        ("schedule_cron_expression", "ALTER TABLE test_scenarios ADD COLUMN schedule_cron_expression VARCHAR(200)"),
        ("schedule_env_id", "ALTER TABLE test_scenarios ADD COLUMN schedule_env_id INTEGER"),
        ("schedule_webhook_url", "ALTER TABLE test_scenarios ADD COLUMN schedule_webhook_url TEXT"),
        ("schedule_task_name", "ALTER TABLE test_scenarios ADD COLUMN schedule_task_name VARCHAR(200)"),
        ("schedule_is_active", "ALTER TABLE test_scenarios ADD COLUMN schedule_is_active BOOLEAN DEFAULT 1"),
    ]


async def ensure_schedule_columns_on_db() -> None:
    """SQLite: add schedule columns if missing (idempotent)."""
    async with async_session() as session:

        def _migrate(sync_conn: Any) -> None:
            r = sync_conn.execute(text("PRAGMA table_info(test_scenarios)"))
            existing = {row[1] for row in r.fetchall()}
            for col, ddl in _schedule_column_ddl():
                if col not in existing:
                    sync_conn.execute(text(ddl))

        await session.run_sync(_migrate)
        await session.commit()


async def persist_schedule_to_db(
    scenario_id: int,
    cron_expression: str,
    env_id: Optional[int],
    webhook_url: Optional[str],
    name: Optional[str],
    is_active: bool,
) -> None:
    async with async_session() as session:
        res = await session.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
        row = res.scalar_one_or_none()
        if not row:
            return
        row.schedule_cron_expression = cron_expression
        row.schedule_env_id = env_id
        row.schedule_webhook_url = webhook_url or None
        row.schedule_task_name = name
        row.schedule_is_active = is_active
        await session.commit()


async def persist_schedule_is_active_db(scenario_id: int, is_active: bool) -> None:
    async with async_session() as session:
        res = await session.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
        row = res.scalar_one_or_none()
        if not row:
            return
        row.schedule_is_active = is_active
        await session.commit()


async def clear_schedule_from_db(scenario_id: int) -> None:
    async with async_session() as session:
        res = await session.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
        row = res.scalar_one_or_none()
        if not row:
            return
        row.schedule_cron_expression = None
        row.schedule_env_id = None
        row.schedule_webhook_url = None
        row.schedule_task_name = None
        row.schedule_is_active = True
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
        if not s.is_active:
            continue
        try:
            add_scheduled_task(
                scenario_id=s.id,
                cron_expression=cron,
                env_id=s.schedule_env_id,
                webhook_url=s.schedule_webhook_url,
                task_name=s.schedule_task_name,
                is_active=s.schedule_is_active if s.schedule_is_active is not None else True,
            )
        except Exception as e:
            print(f"[Scheduler] 从数据库恢复任务失败 scenario_id={s.id}: {e}")


def read_schedule_webhook_sync(scenario_id: int) -> Optional[str]:
    """同步读取场景的定时 Webhook（供 Celery worker 等非 async 上下文使用）。"""
    import sqlite3

    from fastapi_backend.core.autotest_database import INSTANCE_DIR

    path = INSTANCE_DIR / "auto_test.db"
    if not path.exists():
        return None
    try:
        con = sqlite3.connect(str(path))
        try:
            cur = con.execute(
                "SELECT schedule_webhook_url FROM test_scenarios WHERE id = ?",
                (int(scenario_id),),
            )
            row = cur.fetchone()
            if not row or not row[0]:
                return None
            s = str(row[0]).strip()
            return s or None
        finally:
            con.close()
    except Exception:
        return None
