"""PostgreSQL-only validation for the database schedule lease.

The default suite remains runnable without Docker. CI supplies TEST_POSTGRES_URL
so this test exercises the row-count lease against PostgreSQL rather than merely
assuming SQLite's concurrency behavior is equivalent.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutoTestScenario,
    TestSuite as SuiteModel,
    TestSuiteSchedule as SuiteScheduleModel,
    TestSuiteScenario as SuiteScenarioModel,
)
from fastapi_backend.services import suite_schedule_service


POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")


@pytest.mark.asyncio
@pytest.mark.skipif(not POSTGRES_URL, reason="requires TEST_POSTGRES_URL")
async def test_postgresql_schedule_lease_allows_only_one_concurrent_enqueue(monkeypatch):
    engine = create_async_engine(POSTGRES_URL, pool_pre_ping=True)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    dispatched: list[int] = []

    async def _dispatch(execution_id: int) -> None:
        dispatched.append(execution_id)

    monkeypatch.setattr(suite_schedule_service, "AsyncSessionLocal", factory)
    monkeypatch.setattr(suite_schedule_service, "dispatch_suite_execution", _dispatch)
    monkeypatch.setattr(
        suite_schedule_service,
        "get_scheduler",
        lambda: SimpleNamespace(get_job=lambda _job_id: SimpleNamespace(next_run_time=None)),
    )

    async with factory() as db:
        scenario = AutoTestScenario(name="PostgreSQL lease scenario", description="", is_active=True, user_id=99101)
        db.add(scenario)
        await db.flush()
        suite = SuiteModel(name="PostgreSQL lease suite", user_id=99101, kind="scenario")
        db.add(suite)
        await db.flush()
        db.add(SuiteScenarioModel(suite_id=suite.id, scenario_id=scenario.id, sort_order=0))
        schedule = SuiteScheduleModel(
            suite_id=suite.id,
            cron_expression="* * * * *",
            timezone_name="UTC",
            is_active=True,
            max_concurrent=1,
        )
        db.add(schedule)
        await db.commit()
        schedule_id = schedule.id
        suite_id = suite.id

    try:
        await asyncio.gather(
            suite_schedule_service.execute_scheduled_suite(schedule_id),
            suite_schedule_service.execute_scheduled_suite(schedule_id),
        )
        async with factory() as db:
            count = await db.scalar(
                select(func.count())
                .select_from(AutomationExecution)
                .where(
                    AutomationExecution.target_type == "suite",
                    AutomationExecution.target_id == suite_id,
                )
            )
            schedule = await db.get(SuiteScheduleModel, schedule_id)
        assert count == 1
        assert len(dispatched) == 1
        assert schedule.lease_token is None
        assert schedule.lease_expires_at is None
    finally:
        async with factory() as db:
            await db.execute(SuiteModel.__table__.delete().where(SuiteModel.id == suite_id))
            await db.execute(AutoTestScenario.__table__.delete().where(AutoTestScenario.user_id == 99101))
            await db.commit()
        await engine.dispose()
