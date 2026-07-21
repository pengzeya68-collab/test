import asyncio
import io
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import ImportJob
from fastapi_backend.services.har_import import parse_har
from fastapi_backend.services.mock_service import mock_engine
from fastapi_backend.tests.test_autotest_compat import (
    autotest_client,
    autotest_engine,
    autotest_session_factory,
)


def test_har_parser_redacts_credentials_and_ignores_static_assets():
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.test/orders?token=secret&visible=yes",
                        "headers": [
                            {"name": "Authorization", "value": "Bearer secret"},
                            {"name": "Cookie", "value": "session=secret"},
                            {"name": "Content-Type", "value": "application/json"},
                        ],
                        "postData": {"mimeType": "application/json", "text": '{"password":"secret","name":"alice"}'},
                    },
                    "response": {"status": 201},
                    "time": 42,
                },
                {
                    "_resourceType": "image",
                    "request": {"method": "GET", "url": "https://example.test/logo.png"},
                    "response": {"status": 200},
                },
            ]
        }
    }

    candidates = parse_har(__import__("json").dumps(har).encode())

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["headers"]["Authorization"] == "{{AUTHORIZATION}}"
    assert "Cookie" not in candidate["headers"]
    assert "{{TOKEN}}" in candidate["url"]
    assert candidate["payload"]["password"] == "{{PASSWORD}}"
    assert candidate["assert_rules"][0]["expected"] == 201


def test_har_parser_keeps_only_redirect_terminal_and_preserves_safe_metadata():
    response_body = json.dumps({"token": "response-secret", "ok": True}).encode("utf-8")
    har = {
        "log": {
            "entries": [
                {
                    "request": {"method": "GET", "url": "https://example.test/old?token=secret", "headers": []},
                    "response": {"status": 302, "redirectURL": "/new?token=secret", "headers": []},
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.test/new?token=secret",
                        "headers": [],
                        "postData": {
                            "mimeType": "multipart/form-data",
                            "params": [
                                {
                                    "name": "attachment",
                                    "fileName": "C:\\fakepath\\evidence.png",
                                    "contentType": "image/png",
                                },
                            ],
                        },
                    },
                    "response": {
                        "status": 201,
                        "content": {
                            "mimeType": "application/json",
                            "encoding": "base64",
                            "text": __import__("base64").b64encode(response_body).decode("ascii"),
                            "size": len(response_body),
                        },
                    },
                },
            ]
        }
    }

    candidates = parse_har(json.dumps(har).encode())

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["payload"]["attachment"] == {
        "filename": "evidence.png",
        "content_type": "image/png",
        "requires_file_selection": True,
    }
    metadata = candidate["source_metadata"]
    assert len(metadata["redirect_chain"]) == 1
    assert "secret" not in json.dumps(metadata)
    assert metadata["response"]["sha256"]
    assert metadata["response"]["json_sample"]["token"] == "{{TOKEN}}"


def test_mock_status_fault_is_deterministic_when_seeded():
    rule = SimpleNamespace(
        id=7,
        delay_ms=0,
        fault_type="status_error",
        fault_config={"status_code": 503, "random_seed": "repeatable", "trigger_probability": 1},
    )

    response = asyncio.run(mock_engine.generate_response(rule))

    assert response["status"] == 503
    assert response["headers"]["X-TestMaster-Fault"] == "status_error"


@pytest.mark.asyncio
async def test_har_preview_and_commit_create_auditable_import_jobs(autotest_client, autotest_session_factory):
    async def _admin_user():
        return SimpleNamespace(
            id=1,
            username="admin",
            is_admin=True,
            is_super_admin=True,
            is_active=True,
            role_id=None,
        )

    app.dependency_overrides[get_current_user] = _admin_user
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.test/orders/42",
                        "headers": [],
                    },
                    "response": {"status": 200},
                }
            ]
        }
    }
    payload = json.dumps(har).encode("utf-8")

    preview = autotest_client.post(
        "/api/auto-test/import/har",
        files={"file": ("orders.har", io.BytesIO(payload), "application/json")},
        data={"dry_run": "true"},
    )
    assert preview.status_code == 200
    assert preview.json()["import_job_id"]

    commit = autotest_client.post(
        "/api/auto-test/import/har",
        files={"file": ("orders.har", io.BytesIO(payload), "application/json")},
        data={"dry_run": "false", "selected_ids": json.dumps([preview.json()["candidates"][0]["id"]])},
    )
    assert commit.status_code == 200
    assert commit.json()["imported_count"] == 1
    assert commit.json()["import_job_id"]

    async with autotest_session_factory() as session:
        jobs = list((await session.scalars(select(ImportJob))).all())
    assert {job.status for job in jobs} == {"previewed", "completed"}
    completed = next(job for job in jobs if job.status == "completed")
    assert completed.summary["imported_count"] == 1
    assert completed.summary["sensitive_values_redacted"] is True
