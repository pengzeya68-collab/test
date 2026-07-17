from types import SimpleNamespace

import pytest

from fastapi_backend.services import autotest_scheduler as scheduler_module


@pytest.fixture(autouse=True)
def clear_scheduler_cache():
    scheduler_module.scheduled_tasks.clear()
    yield
    scheduler_module.scheduled_tasks.clear()


def _persisted_job(user_id=42):
    return SimpleNamespace(
        id="auto_sched_7",
        args=[7, 3, "auto_sched_7", user_id],
        trigger=SimpleNamespace(fields=["wrong"] * 8),
        name="persisted job",
        next_run_time=SimpleNamespace(isoformat=lambda: "2026-07-11T09:00:00+08:00"),
    )


def test_rebuilt_task_keeps_owner_and_uses_database_cron(monkeypatch):
    job = _persisted_job()
    monkeypatch.setattr(
        scheduler_module,
        "get_scheduler",
        lambda: SimpleNamespace(get_job=lambda _task_id: job),
    )
    monkeypatch.setattr(
        scheduler_module,
        "_schedule_meta_from_db",
        lambda scenario_id, user_id=None: {
            "cron_expression": "0 9 * * *",
            "webhook_url": None,
            "env_id": 3,
            "name": "daily",
        },
    )

    task = scheduler_module.get_scheduled_task(job.id)

    assert task["user_id"] == 42
    assert task["cron_expression"] == "0 9 * * *"


def test_rebuilt_tasks_are_filtered_by_owner(monkeypatch):
    job = _persisted_job(user_id=99)
    fake_scheduler = SimpleNamespace(get_jobs=lambda: [job], get_job=lambda _task_id: job)
    monkeypatch.setattr(scheduler_module, "get_scheduler", lambda: fake_scheduler)
    monkeypatch.setattr(
        scheduler_module,
        "_schedule_meta_from_db",
        lambda scenario_id, user_id=None: {"cron_expression": "*/5 * * * *"},
    )

    assert scheduler_module.get_all_scheduled_tasks(user_id=42) == []
    tasks = scheduler_module.get_all_scheduled_tasks(user_id=99)
    assert len(tasks) == 1
    assert tasks[0]["user_id"] == 99
