from types import SimpleNamespace

import pytest

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
    monkeypatch.setattr(module, "decrypt", lambda value: "decrypted-password")
    async def effective(_db, _env_id, user_id=None):
        assert user_id == 42
        return [
            {"name": "API_URL", "value": "https://env.example"},
            {"name": "api_token", "value": "env-token"},
        ]
    monkeypatch.setattr(module, "get_effective_variables", effective)

    globals_ = [
        SimpleNamespace(name="PASSWORD", value="cipher", is_encrypted=True),
        SimpleNamespace(name="API_URL", value="https://global.example", is_encrypted=False),
        SimpleNamespace(name="PUBLIC_NAME", value="tester", is_encrypted=False),
    ]
    environment = SimpleNamespace(id=7, env_name="测试环境", base_url="https://app.example")
    db = FakeSession([FakeResult(items=globals_), FakeResult(one=environment)])

    result = await module.get_runtime_config(
        environment_id=7,
        current_user=SimpleNamespace(id=42),
        autotest_db=db,
    )

    assert result["base_url"] == "https://app.example"
    assert result["environment_name"] == "测试环境"
    assert result["variables"]["PASSWORD"] == "decrypted-password"
    assert result["variables"]["API_URL"] == "https://env.example"
    assert result["variables"]["api_token"] == "env-token"
    assert result["variables"]["PUBLIC_NAME"] == "tester"
    assert result["secret_keys"] == ["PASSWORD", "api_token"]


@pytest.mark.asyncio
async def test_runtime_config_rejects_environment_not_owned_by_user(monkeypatch):
    monkeypatch.setattr(module.settings, "UI_AUTOMATION_ENABLED", True)
    db = FakeSession([FakeResult(items=[]), FakeResult(one=None)])

    with pytest.raises(Exception) as exc:
        await module.get_runtime_config(
            environment_id=999,
            current_user=SimpleNamespace(id=42),
            autotest_db=db,
        )

    assert getattr(exc.value, "code", None) == "ENVIRONMENT_NOT_FOUND"

