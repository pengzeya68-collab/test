from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml

from fastapi_backend import main
from fastapi_backend.core.config import Settings, settings, validate_production_database
from fastapi_backend.services import autotest_schedule_persistence


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_production_requires_postgresql_database_url():
    config = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="sqlite+aiosqlite:///./instance/testmaster.db",
        SECRET_KEY="test-secret",
        ADMIN_PASSWORD="test-password",
        ADMIN_SECRET_KEY="test-admin-secret",
    )

    with pytest.raises(RuntimeError, match="Production requires PostgreSQL"):
        validate_production_database(config)


@pytest.mark.asyncio
async def test_production_rejects_runtime_create_all(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTO_CREATE_TABLES_ON_STARTUP", True)

    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        await main.create_tables()


@pytest.mark.asyncio
async def test_production_skips_legacy_schedule_runtime_ddl(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    def _unexpected_session():
        raise AssertionError("production must not open a runtime DDL session")

    monkeypatch.setattr(autotest_schedule_persistence, "async_session", _unexpected_session)
    await autotest_schedule_persistence.ensure_schedule_columns_on_db()


def test_compose_runs_single_migration_gate_before_services():
    compose = yaml.safe_load((PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert "alembic" in services["migrate"]["command"]
    assert "upgrade head" in services["migrate"]["command"]
    assert services["migrate"]["restart"] == "no"
    assert "AUTO_CREATE_TABLES_ON_STARTUP=false" in services["backend"]["environment"]
    assert services["backend"]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
    assert services["celery-worker"]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
    assert services["backend"]["image"] == services["celery-worker"]["image"] == services["migrate"]["image"]


def test_production_environment_template_requires_migrations_not_runtime_ddl():
    template = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "AUTO_CREATE_TABLES_ON_STARTUP=false" in template


@pytest.mark.asyncio
async def test_production_startup_fails_closed_when_automation_storage_is_invalid(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTO_CREATE_TABLES_ON_STARTUP", False)
    monkeypatch.setattr(main, "ensure_dev_tables", AsyncMock())
    monkeypatch.setattr(main, "ensure_desktop_admin", AsyncMock())
    monkeypatch.setattr(
        main,
        "init_auto_test_runtime",
        AsyncMock(side_effect=RuntimeError("schema is not at head")),
    )

    with pytest.raises(RuntimeError, match="schema is not at head"):
        async with main.lifespan(None):
            pass
