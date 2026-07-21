"""Deployment safety checks for an empty database and the latest rollback."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = PROJECT_ROOT / "fastapi_backend" / "alembic.ini"
HEAD_REVISION = "ac1d2e3f4a5b"
PRE_FEEDBACK_REVISION = "ab1c2d3e4f5a"
WEBHOOK_REVISION = "aa0b1c2d3e4f"
PRE_WEBHOOK_REVISION = "a9d0e1f2a3b4"


def _alembic(env: dict[str, str], *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_CONFIG), *arguments],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_empty_database_bootstraps_head_and_execution_policy_rolls_back(tmp_path):
    database = tmp_path / "fresh-testmaster.db"
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite+aiosqlite:///{database.as_posix()}",
            "ENVIRONMENT": "testing",
            "SECRET_KEY": "alembic-bootstrap-test-key",
            "ADMIN_PASSWORD": "alembic-bootstrap-test-password",
            "ADMIN_SECRET_KEY": "alembic-bootstrap-test-admin-key",
        }
    )

    bootstrapped = _alembic(env, "upgrade", "head")
    assert bootstrapped.returncode == 0, bootstrapped.stderr
    with sqlite3.connect(database) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        version = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert {"users", "automation_webhooks", "automation_webhook_receipts", "ai_analysis_feedback"}.issubset(tables)
    assert version == HEAD_REVISION
    with sqlite3.connect(database) as connection:
        schedule_columns = {row[1] for row in connection.execute("PRAGMA table_info(test_suite_schedules)")}
    assert {"execution_timeout_seconds", "max_retries"}.issubset(schedule_columns)
    with sqlite3.connect(database) as connection:
        scenario_schedule_columns = {row[1] for row in connection.execute("PRAGMA table_info(test_scenarios)")}
    assert {
        "schedule_cron_expression",
        "schedule_env_id",
        "schedule_webhook_url",
        "schedule_task_name",
        "schedule_is_active",
    }.issubset(scenario_schedule_columns)

    feedback_rolled_back = _alembic(env, "downgrade", PRE_FEEDBACK_REVISION)
    assert feedback_rolled_back.returncode == 0, feedback_rolled_back.stderr
    with sqlite3.connect(database) as connection:
        tables_after_feedback_rollback = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        scenario_columns_after_feedback_rollback = {
            row[1] for row in connection.execute("PRAGMA table_info(test_scenarios)")
        }
    assert "ai_analysis_feedback" not in tables_after_feedback_rollback
    assert "schedule_cron_expression" not in scenario_columns_after_feedback_rollback
    assert "schedule_is_active" not in scenario_columns_after_feedback_rollback
    feedback_upgraded_again = _alembic(env, "upgrade", HEAD_REVISION)
    assert feedback_upgraded_again.returncode == 0, feedback_upgraded_again.stderr

    policy_rolled_back = _alembic(env, "downgrade", WEBHOOK_REVISION)
    assert policy_rolled_back.returncode == 0, policy_rolled_back.stderr
    with sqlite3.connect(database) as connection:
        schedule_columns_after_policy_rollback = {
            row[1] for row in connection.execute("PRAGMA table_info(test_suite_schedules)")
        }
        policy_rollback_version = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert "execution_timeout_seconds" not in schedule_columns_after_policy_rollback
    assert "max_retries" not in schedule_columns_after_policy_rollback
    assert policy_rollback_version == WEBHOOK_REVISION

    policy_upgraded_again = _alembic(env, "upgrade", HEAD_REVISION)
    assert policy_upgraded_again.returncode == 0, policy_upgraded_again.stderr

    rolled_back = _alembic(env, "downgrade", PRE_WEBHOOK_REVISION)
    assert rolled_back.returncode == 0, rolled_back.stderr
    with sqlite3.connect(database) as connection:
        tables_after_downgrade = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        version_after_downgrade = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert "automation_webhooks" not in tables_after_downgrade
    assert "automation_webhook_receipts" not in tables_after_downgrade
    assert version_after_downgrade == PRE_WEBHOOK_REVISION

    upgraded_again = _alembic(env, "upgrade", HEAD_REVISION)
    assert upgraded_again.returncode == 0, upgraded_again.stderr
    with sqlite3.connect(database) as connection:
        tables_after_upgrade = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"automation_webhooks", "automation_webhook_receipts"}.issubset(tables_after_upgrade)


def test_empty_database_never_silently_bootstraps_a_requested_old_revision(tmp_path):
    database = tmp_path / "old-revision-target.db"
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite+aiosqlite:///{database.as_posix()}",
            "ENVIRONMENT": "testing",
            "SECRET_KEY": "alembic-old-target-test-key",
            "ADMIN_PASSWORD": "alembic-old-target-test-password",
            "ADMIN_SECRET_KEY": "alembic-old-target-test-admin-key",
        }
    )

    old_target = _alembic(env, "upgrade", WEBHOOK_REVISION)
    assert old_target.returncode != 0
    assert "空数据库只能执行 'alembic upgrade head'" in old_target.stderr
    with sqlite3.connect(database) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == set()
