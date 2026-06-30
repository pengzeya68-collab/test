import io
import json
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.database import Base as AutoTestBase
from fastapi_backend.main import app
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup, AutoTestScenario
from fastapi_backend.services.autotest_execution import execute_assertions
from fastapi_backend.services.autotest_jmeter_service import export_cases_to_jmx, import_jmx_to_cases


TEST_AUTOTEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def autotest_engine():
    engine = create_async_engine(
        TEST_AUTOTEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(AutoTestBase.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(AutoTestBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def autotest_session_factory(autotest_engine):
    return async_sessionmaker(autotest_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def autotest_client(client, autotest_session_factory):
    from fastapi_backend.deps.auth import get_current_user

    async def _override_get_autotest_db():
        async with autotest_session_factory() as session:
            yield session

    async def _override_current_user():
        from types import SimpleNamespace

        return SimpleNamespace(
            id=1,
            username="tester",
            is_admin=False,
            is_super_admin=False,
            is_active=True,
            role_id=None,
        )

    app.dependency_overrides[get_autotest_db] = _override_get_autotest_db
    app.dependency_overrides[get_current_user] = _override_current_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_autotest_db, None)
        app.dependency_overrides.pop(get_current_user, None)


async def _create_group(session_factory, name="默认分组"):
    async with session_factory() as session:
        group = AutoTestGroup(name=name, parent_id=None, user_id=1)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group


async def _create_scenario(session_factory, name="默认场景"):
    async with session_factory() as session:
        scenario = AutoTestScenario(name=name, description="desc", is_active=True, user_id=1)
        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)
        return scenario


class TestAutoTestCompatibility:
    @pytest.mark.asyncio
    async def test_create_case_accepts_group_id(self, autotest_client, autotest_session_factory):
        group = await _create_group(autotest_session_factory, "创建分组")

        response = autotest_client.post(
            "/api/auto-test/cases/",
            json={
                "group_id": group.id,
                "name": "创建用例",
                "method": "GET",
                "url": "http://example.com/api/test",
                "headers": {},
                "params": {},
                "payload": None,
                "assertions": [],
                "extractors": [],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["group_id"] == group.id
        assert data["name"] == "创建用例"

    @pytest.mark.asyncio
    async def test_scenario_dataset_upsert_without_body_scenario_id(self, autotest_client, autotest_session_factory):
        scenario = await _create_scenario(autotest_session_factory, "数据集场景")

        response = autotest_client.post(
            f"/api/auto-test/scenarios/{scenario.id}/dataset",
            json={
                "name": "默认数据集",
                "data_matrix": {
                    "columns": ["username", "password"],
                    "rows": [["u1", "p1"], ["u2", "p2"]],
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == scenario.id
        assert data["data_matrix"]["columns"] == ["username", "password"]

    @pytest.mark.asyncio
    async def test_postman_import_dry_run_does_not_persist_cases(self, autotest_client, autotest_session_factory):
        collection = {
            "info": {"name": "DryRun Collection"},
            "item": [
                {
                    "name": "登录接口",
                    "request": {
                        "method": "POST",
                        "url": {"raw": "http://example.com/api/login"},
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "body": {"mode": "raw", "raw": '{"username":"u","password":"p"}'},
                    },
                }
            ],
        }

        response = autotest_client.post(
            "/api/auto-test/import/postman",
            files={"file": ("collection.json", io.BytesIO(json.dumps(collection).encode("utf-8")), "application/json")},
            data={"dry_run": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 0
        assert len(data["cases"]) == 1
        assert data["cases"][0]["name"] == "登录接口"

        async with autotest_session_factory() as session:
            result = await session.execute(AutoTestCase.__table__.select())
            assert len(result.fetchall()) == 0

    @pytest.mark.asyncio
    async def test_jmeter_group_export_supports_get_query(self, autotest_client, autotest_session_factory):
        group = await _create_group(autotest_session_factory, "导出分组")
        async with autotest_session_factory() as session:
            case = AutoTestCase(
                group_id=group.id,
                name="导出用例",
                method="GET",
                url="http://example.com/api/export",
                headers={},
                params={},
                user_id=1,
            )
            session.add(case)
            await session.commit()

        response = autotest_client.get(f"/api/auto-test/export/jmeter/cases?group_id={group.id}")

        assert response.status_code == 200
        assert "xml" in response.headers["content-type"] or "octet-stream" in response.headers["content-type"]
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_postman_import_with_nested_folder(self, autotest_client, autotest_session_factory):
        root_group = await _create_group(autotest_session_factory, "根分组")
        collection = {
            "info": {"name": "Nested Collection"},
            "item": [
                {
                    "name": "用户模块",
                    "item": [
                        {
                            "name": "获取用户详情",
                            "request": {
                                "method": "GET",
                                "url": {"raw": "http://example.com/api/users/1"},
                            },
                        }
                    ],
                }
            ],
        }

        response = autotest_client.post(
            "/api/auto-test/import/postman",
            files={"file": ("collection.json", io.BytesIO(json.dumps(collection).encode("utf-8")), "application/json")},
            data={"dry_run": "false", "target_group_id": str(root_group.id)},
        )

        assert response.status_code == 200
        assert response.json()["imported_count"] == 1

    def test_jmeter_round_trip_preserves_headers(self):
        cases = [
            {
                "name": "带请求头用例",
                "method": "POST",
                "url": "https://example.com/api/login",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {{token}}",
                },
                "payload": {"username": "tester"},
            }
        ]

        jmx = export_cases_to_jmx(cases)
        imported_cases = import_jmx_to_cases(jmx)

        assert len(imported_cases) >= 1
        assert imported_cases[0]["headers"]["Content-Type"] == "application/json"
        assert imported_cases[0]["headers"]["Authorization"] == "Bearer {{token}}"

    def test_execute_assertions_supports_json_body_and_symbol_operators(self):
        rules = [
            {"target": "status_code", "operator": "==", "expected": 200},
            {"target": "json_body.message", "operator": "contains", "expected": "success"},
            {"target": "json_body.data.count", "operator": ">=", "expected": 2},
        ]

        result = execute_assertions(
            rules,
            200,
            {"message": "login success", "data": {"count": 2}},
        )

        assert result["passed"] is True
