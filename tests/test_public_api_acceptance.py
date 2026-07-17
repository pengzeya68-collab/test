"""Public-network acceptance tests for the packaged interface automation engine.

Run explicitly with TESTMASTER_PUBLIC_BASE_URL and credentials. These tests create
temporary TestMaster assets and call stable public APIs through TestMaster itself.
"""

import json
import os
import time
import uuid

import pytest
import requests


pytestmark = [pytest.mark.remote, pytest.mark.external, pytest.mark.regression]


@pytest.fixture(scope="module")
def public_client():
    base_url = os.getenv("TESTMASTER_PUBLIC_BASE_URL")
    username = os.getenv("TESTMASTER_PUBLIC_USER")
    password = os.getenv("TESTMASTER_PUBLIC_PASSWORD")
    if not all((base_url, username, password)):
        pytest.skip("Set TESTMASTER_PUBLIC_BASE_URL/USER/PASSWORD to run public API acceptance")
    session = requests.Session()
    login = session.post(
        f"{base_url.rstrip('/')}/api/v1/auth/login",
        json={"username": username, "password": password}, timeout=20,
    )
    assert login.status_code == 200, login.text
    session.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return base_url.rstrip("/"), session


def test_public_send_post_body_auth_and_variables(public_client):
    base_url, session = public_client
    response = session.post(
        f"{base_url}/api/auto-test/send",
        json={
            "method": "POST",
            "url": "https://postman-echo.com/post?run={{run_id}}",
            "variables": {"run_id": "testmaster-public"},
            "headers": {"X-TestMaster-Probe": "public-acceptance"},
            "body_type": "json",
            "body": {"message": "hello", "count": 0, "enabled": False},
            "request_config": {
                "auth": {"type": "bearer", "token": "public-demo-token"},
                "timeout_ms": 20000,
                "retry": {"count": 1, "status_codes": [503]},
                "follow_redirects": True,
            },
        }, timeout=30,
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["response_content"]["args"]["run"] == "testmaster-public"
    assert result["response_content"]["json"] == {"message": "hello", "count": 0, "enabled": False}
    assert result["response_content"]["headers"]["authorization"] == "Bearer public-demo-token"
    assert result["request"]["headers"]["authorization"] == "******"


def test_public_two_api_scenario_extracts_variable_and_asserts(public_client):
    base_url, session = public_client
    created = {"group": None, "scenario": None, "cases": []}
    suffix = uuid.uuid4().hex[:8]

    def api(method, path, **kwargs):
        return session.request(method, f"{base_url}{path}", timeout=30, **kwargs)

    try:
        group = api("POST", "/api/auto-test/groups", json={"name": f"公网验收_{suffix}"})
        assert group.status_code == 201, group.text
        created["group"] = group.json()["id"]

        first = api("POST", "/api/auto-test/cases", json={
            "group_id": created["group"], "name": "公网步骤1-读取文章", "method": "GET",
            "url": "https://jsonplaceholder.typicode.com/posts/1", "body_type": "none",
            "assertions": [{"target": "response_body", "expression": "$.id", "operator": "==", "expected": 1}],
            "extractors": [{"variableName": "publicUserId", "extractorType": "jsonpath", "expression": "$.userId"}],
            "request_config": {"timeout_ms": 20000, "retry": {"count": 1, "status_codes": [503]}},
        })
        assert first.status_code == 201, first.text
        created["cases"].append(first.json()["id"])

        second = api("POST", "/api/auto-test/cases", json={
            "group_id": created["group"], "name": "公网步骤2-使用提取变量", "method": "GET",
            "url": "https://jsonplaceholder.typicode.com/users/{{publicUserId}}", "body_type": "none",
            "assertions": [
                {"target": "response_body", "expression": "$.id", "operator": "==", "expected": 1},
                {"target": "response_body", "expression": "$.username", "operator": "not_empty", "expected": ""},
            ],
            "request_config": {"timeout_ms": 20000, "retry": {"count": 1, "status_codes": [503]}},
        })
        assert second.status_code == 201, second.text
        created["cases"].append(second.json()["id"])

        scenario = api("POST", "/api/auto-test/scenarios", json={"name": f"公网双接口变量链_{suffix}"})
        assert scenario.status_code in (200, 201), scenario.text
        created["scenario"] = scenario.json()["id"]
        for order, case_id in enumerate(created["cases"]):
            step = api("POST", f"/api/auto-test/scenarios/{created['scenario']}/steps", json={
                "api_case_id": case_id, "step_order": order, "is_active": True,
            })
            assert step.status_code in (200, 201), step.text

        run = api("POST", f"/api/auto-test/scenarios/{created['scenario']}/debug", json={"context_vars": {}})
        assert run.status_code == 200, run.text
        result = run.json()
        assert result["success"] is True, json.dumps(result, ensure_ascii=False, indent=2)
        assert len(result["step_results"]) == 2
        assert result["context_vars"]["publicUserId"] == 1
        assert result["step_results"][1]["status_code"] == 200
        assert result["step_results"][1]["assertions"]["failed"] == []
    finally:
        if created["scenario"]:
            api("DELETE", f"/api/auto-test/scenarios/{created['scenario']}")
        for case_id in reversed(created["cases"]):
            api("DELETE", f"/api/auto-test/cases/{case_id}")
        if created["group"]:
            api("DELETE", f"/api/auto-test/groups/{created['group']}")
