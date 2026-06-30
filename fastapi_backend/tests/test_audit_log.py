"""
审计日志服务测试

覆盖：
1. 记录 create 日志
2. 记录 update 日志（含 before/after detail）
3. 记录 failed 日志
4. 按 user_id 过滤查询
5. 按 resource_type + resource_id 过滤查询
6. 按时间范围过滤查询
7. 统计信息查询
8. 审计日志记录失败时不影响主流程（mock 数据库异常）

注意：AuditService.log 写入使用独立 session（与业务事务隔离）。
为保证测试中“写入 session”与“查询 session”共享同一内存库，
使用 StaticPool 让所有 session 复用同一连接，并覆盖 AuditService._session_factory。
"""

from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.core.database import Base
from fastapi_backend.services.audit_service import AuditService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def audit_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def audit_session_factory(audit_engine):
    return async_sessionmaker(audit_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def patched_audit_service(audit_session_factory):
    """覆盖 AuditService 的会话工厂，使其写入测试内存库。"""
    original = AuditService._session_factory
    AuditService._session_factory = audit_session_factory
    try:
        yield audit_session_factory
    finally:
        AuditService._session_factory = original


@pytest.fixture
def now_utc():
    return datetime.now(timezone.utc)


# ========== 测试用例 ==========


@pytest.mark.asyncio
async def test_record_create_log(patched_audit_service, audit_session_factory):
    """1. 记录一条 create 日志，并能查询到。"""
    await AuditService.log(
        db=None,
        user_id=1,
        username="alice",
        action="create",
        resource_type="scenario",
        resource_id=10,
        resource_name="登录场景",
    )

    async with audit_session_factory() as session:
        result = await AuditService.query_logs(db=session, page=1, page_size=10)

    assert result["total"] >= 1
    item = result["items"][0]
    assert item["action"] == "create"
    assert item["resource_type"] == "scenario"
    assert item["resource_id"] == 10
    assert item["resource_name"] == "登录场景"
    assert item["username"] == "alice"
    assert item["status"] == "success"


@pytest.mark.asyncio
async def test_record_update_log_with_detail(patched_audit_service, audit_session_factory):
    """2. 记录一条 update 日志（含 before/after detail）。"""
    detail = {
        "before": {"name": "旧名称", "is_active": True},
        "after": {"name": "新名称", "is_active": False},
    }
    await AuditService.log(
        db=None,
        user_id=2,
        username="bob",
        action="update",
        resource_type="variable",
        resource_id=5,
        resource_name="API_KEY",
        detail=detail,
    )

    async with audit_session_factory() as session:
        result = await AuditService.query_logs(db=session, action="update")

    assert result["total"] >= 1
    item = result["items"][0]
    assert item["action"] == "update"
    assert item["detail"] == detail


@pytest.mark.asyncio
async def test_record_failed_log(patched_audit_service, audit_session_factory):
    """3. 记录一条 failed 日志，含失败原因。"""
    await AuditService.log(
        db=None,
        user_id=1,
        username="alice",
        action="delete",
        resource_type="scenario",
        resource_id=99,
        status="failed",
        error_message="场景不存在",
    )

    async with audit_session_factory() as session:
        result = await AuditService.query_logs(db=session)

    # 在结果中找到 failed 日志
    failed = [i for i in result["items"] if i["status"] == "failed"]
    assert len(failed) >= 1
    assert failed[0]["error_message"] == "场景不存在"


@pytest.mark.asyncio
async def test_query_by_user_id(patched_audit_service, audit_session_factory):
    """4. 按 user_id 过滤查询。"""
    await AuditService.log(
        db=None, user_id=1, username="alice", action="create", resource_type="scenario", resource_id=1
    )
    await AuditService.log(
        db=None, user_id=2, username="bob", action="create", resource_type="scenario", resource_id=2
    )

    async with audit_session_factory() as session:
        result = await AuditService.query_logs(db=session, user_id=2)

    assert result["total"] >= 1
    assert all(i["user_id"] == 2 for i in result["items"])


@pytest.mark.asyncio
async def test_query_by_resource_type_and_id(patched_audit_service, audit_session_factory):
    """5. 按 resource_type + resource_id 过滤查询。"""
    await AuditService.log(
        db=None, user_id=1, username="alice", action="create", resource_type="scenario", resource_id=100
    )
    await AuditService.log(
        db=None, user_id=1, username="alice", action="create", resource_type="case", resource_id=100
    )
    await AuditService.log(
        db=None, user_id=1, username="alice", action="create", resource_type="scenario", resource_id=200
    )

    async with audit_session_factory() as session:
        result = await AuditService.query_logs(
            db=session, resource_type="scenario", resource_id=100
        )

    assert result["total"] >= 1
    for item in result["items"]:
        assert item["resource_type"] == "scenario"
        assert item["resource_id"] == 100


@pytest.mark.asyncio
async def test_query_by_time_range(patched_audit_service, audit_session_factory, now_utc):
    """6. 按时间范围过滤查询。"""
    await AuditService.log(
        db=None, user_id=1, username="alice", action="create", resource_type="scenario", resource_id=1
    )

    # 范围包含当前时刻 → 应能查到
    async with audit_session_factory() as session:
        included = await AuditService.query_logs(
            db=session,
            start_time=now_utc - timedelta(hours=1),
            end_time=now_utc + timedelta(hours=1),
        )
    assert included["total"] >= 1

    # 起始时间在未来 → 应查不到
    async with audit_session_factory() as session:
        excluded = await AuditService.query_logs(
            db=session,
            start_time=now_utc + timedelta(hours=1),
            end_time=now_utc + timedelta(hours=2),
        )
    assert excluded["total"] == 0


@pytest.mark.asyncio
async def test_stats(patched_audit_service, audit_session_factory):
    """7. 统计信息查询（按 action / resource_type / user 分组）。"""
    await AuditService.log(
        db=None, user_id=1, username="alice", action="create", resource_type="scenario", resource_id=1
    )
    await AuditService.log(
        db=None, user_id=1, username="alice", action="execute", resource_type="scenario", resource_id=1
    )
    await AuditService.log(
        db=None, user_id=2, username="bob", action="delete", resource_type="case", resource_id=3
    )

    async with audit_session_factory() as session:
        stats = await AuditService.stats(db=session)

    assert stats["by_action"].get("create", 0) >= 1
    assert stats["by_action"].get("execute", 0) >= 1
    assert stats["by_action"].get("delete", 0) >= 1
    assert stats["by_resource_type"].get("scenario", 0) >= 2
    assert stats["by_resource_type"].get("case", 0) >= 1
    assert stats["by_user"].get("alice", 0) >= 2
    assert stats["by_user"].get("bob", 0) >= 1


@pytest.mark.asyncio
async def test_audit_failure_does_not_affect_main_flow(audit_session_factory):
    """8. 审计日志记录失败时不影响主流程（mock 数据库异常）。"""
    original = AuditService._session_factory

    class _FailingSession:
        def add(self, *args, **kwargs):
            pass

        async def commit(self):
            raise RuntimeError("模拟数据库宕机")

        async def rollback(self):
            pass

    class _FailingFactory:
        def __call__(self):
            @asynccontextmanager
            async def _cm():
                yield _FailingSession()

            return _cm()

    # 注入会抛异常的会话工厂
    AuditService._session_factory = _FailingFactory()
    try:
        # 调用 log 不应抛异常
        await AuditService.log(
            db=None,
            user_id=1,
            username="alice",
            action="create",
            resource_type="scenario",
            resource_id=1,
        )
        main_flow_ok = True
    except Exception:
        main_flow_ok = False
    finally:
        AuditService._session_factory = original

    assert main_flow_ok, "审计日志失败不应影响主业务流程"


@pytest.mark.asyncio
async def test_detail_truncation(patched_audit_service, audit_session_factory):
    """补充：detail 超过 10KB 时应被截断，不影响写入。"""
    big_detail = {"payload": "x" * (11 * 1024)}
    await AuditService.log(
        db=None,
        user_id=1,
        username="alice",
        action="update",
        resource_type="scenario",
        resource_id=1,
        detail=big_detail,
    )

    async with audit_session_factory() as session:
        result = await AuditService.query_logs(db=session, action="update")

    assert result["total"] >= 1
    # detail 字段被截断（以 truncated 标记结尾），原大对象不会原样存入
    item = result["items"][0]
    assert item["detail"] is None or "truncated" in str(item["detail"]) or len(str(item["detail"])) < 11 * 1024
