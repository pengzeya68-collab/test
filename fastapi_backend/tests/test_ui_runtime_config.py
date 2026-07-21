from types import SimpleNamespace

import pytest
from fastapi import Response
from fastapi_backend.core.exceptions import BusinessException

from fastapi_backend.routers import ui_automation as module


class FakeScalars:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items


class FakeResult:
    def __init__(self, *, items=None, one=None):
        self.items = items or []
        self.one = one

    def scalars(self):
        return FakeScalars(self.items)

    def scalar_one_or_none(self):
        return self.one


class FakeSession:
    def __init__(self, results):
        self.results = list(results)

    async def execute(self, _query):
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_runtime_config_merges_globals_environment_and_masks_metadata(monkeypatch):
    monkeypatch.setattr(module.settings, "UI_AUTOMATION_ENABLED", True)

    async def resolve(_db, *, user_id, environment_id):
        assert user_id == 42
        assert environment_id == 7
        return {
            "id": 7,
            "name": "测试环境",
            "base_url": "https://app.example",
            "services": [],
            "variables": {
                "PASSWORD": "decrypted-password",
                "API_URL": "https://env.example",
                "api_token": "env-token",
                "PUBLIC_NAME": "tester",
            },
            "secret_keys": ["PASSWORD", "api_token"],
        }

    monkeypatch.setattr(module, "resolve_runtime_environment", resolve)
    response = Response()

    result = await module.get_runtime_config(
        response=response,
        environment_id=7,
        current_user=SimpleNamespace(id=42),
        autotest_db=FakeSession([]),
    )

    assert result["base_url"] == "https://app.example"
    assert result["environment_name"] == "测试环境"
    assert result["variables"]["PASSWORD"] == "decrypted-password"
    assert result["variables"]["API_URL"] == "https://env.example"
    assert result["variables"]["api_token"] == "env-token"
    assert result["variables"]["PUBLIC_NAME"] == "tester"
    assert result["secret_keys"] == ["PASSWORD", "api_token"]
    assert response.headers["Cache-Control"] == "private, no-store"


@pytest.mark.asyncio
async def test_runtime_config_rejects_environment_not_owned_by_user(monkeypatch):
    monkeypatch.setattr(module.settings, "UI_AUTOMATION_ENABLED", True)

    async def resolve(_db, *, user_id, environment_id):
        raise BusinessException("Environment not found", code="ENVIRONMENT_NOT_FOUND", status_code=404)

    monkeypatch.setattr(module, "resolve_runtime_environment", resolve)

    with pytest.raises(Exception) as exc:
        await module.get_runtime_config(
            response=Response(),
            environment_id=999,
            current_user=SimpleNamespace(id=42),
            autotest_db=FakeSession([]),
        )

    assert getattr(exc.value, "code", None) == "ENVIRONMENT_NOT_FOUND"
