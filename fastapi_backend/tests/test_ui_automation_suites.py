import pytest
from types import SimpleNamespace

from fastapi_backend.core.config import settings
from fastapi_backend.deps.auth import get_current_active_user, get_current_user
from fastapi_backend.main import app


@pytest.fixture(autouse=True)
def enable_ui_automation():
    original = settings.UI_AUTOMATION_ENABLED
    settings.UI_AUTOMATION_ENABLED = True
    yield
    settings.UI_AUTOMATION_ENABLED = original


@pytest.fixture(autouse=True)
def current_user():
    async def user():
        return SimpleNamespace(
            id=1, username="suite-user", is_active=True, is_admin=True, is_super_admin=True, role_id=None
        )

    app.dependency_overrides[get_current_active_user] = user
    app.dependency_overrides[get_current_user] = user
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


def create_versioned_case(client, name, suffix):
    case = client.post("/api/ui-automation/cases", json={"name": name, "base_url": "https://example.com"}).json()
    saved = client.put(
        f"/api/ui-automation/cases/{case['id']}/steps",
        json={
            "steps": [
                {"id": f"suite-{suffix}-open", "order": 10, "type": "goto", "input": {"url": "/{{path}}"}},
                {
                    "id": f"suite-{suffix}-assert",
                    "order": 20,
                    "type": "assert_title",
                    "input": {"expected": "{{title}}"},
                },
            ]
        },
    )
    assert saved.status_code == 200, saved.text
    return case, client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()


@pytest.mark.asyncio
async def test_suite_crud_and_data_driven_execution_plan(client):
    case_a, version_a = create_versioned_case(client, "Data case", "a")
    case_b, version_b = create_versioned_case(client, "Checkout case", "b")

    created = client.post(
        "/api/ui-automation/suites",
        json={
            "name": "核心回归套件",
            "description": "登录到下单",
            "stop_on_first_failure": True,
        },
    )
    assert created.status_code == 200, created.text
    suite = created.json()

    items = client.put(
        f"/api/ui-automation/suites/{suite['id']}/items",
        json=[
            {
                "case_id": case_a["id"],
                "pinned_version_id": version_a["id"],
                "order": 10,
                "data_source": {
                    "rows": [
                        {"path": "product/1", "title": "商品一"},
                        {"path": "product/2", "title": "商品二"},
                    ]
                },
                "overrides": {"tenant": "enterprise"},
            },
            {"case_id": case_b["id"], "pinned_version_id": version_b["id"], "order": 20},
        ],
    )
    assert items.status_code == 200, items.text
    assert len(items.json()["items"]) == 2

    plan_response = client.get(f"/api/ui-automation/suites/{suite['id']}/execution-plan")
    assert plan_response.status_code == 200, plan_response.text
    plan = plan_response.json()
    assert plan["stop_on_first_failure"] is True
    assert len(plan["entries"]) == 3
    assert plan["entries"][0]["variables"] == {"tenant": "enterprise", "path": "product/1", "title": "商品一"}
    assert plan["entries"][1]["iteration"] == 1
    assert plan["entries"][2]["case_id"] == case_b["id"]
    assert plan["entries"][0]["snapshot"]["steps"][0]["input"]["url"] == "/{{path}}"

    aggregate_run = client.post("/api/ui-automation/runs", json={"suite_id": suite["id"], "trigger_type": "manual"})
    assert aggregate_run.status_code == 200, aggregate_run.text
    assert aggregate_run.json()["suite_id"] == suite["id"]
    assert aggregate_run.json()["total_steps"] == 6
    suite_runs = client.get(f"/api/ui-automation/runs?suite_id={suite['id']}")
    assert suite_runs.status_code == 200
    assert suite_runs.json()["total"] == 1
    listed = client.get("/api/ui-automation/suites")
    assert listed.status_code == 200
    assert any(item["id"] == suite["id"] for item in listed.json()["items"])

    duplicate = client.put(
        f"/api/ui-automation/suites/{suite['id']}/items",
        json=[
            {"case_id": case_a["id"], "order": 10},
            {"case_id": case_a["id"], "order": 20},
        ],
    )
    assert duplicate.status_code == 422

    deleted = client.delete(f"/api/ui-automation/suites/{suite['id']}")
    assert deleted.status_code == 200
    assert client.get(f"/api/ui-automation/suites/{suite['id']}").status_code == 404
