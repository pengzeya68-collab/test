"""
TestMaster 测试配置 (优化版)

优化点:
1. Schema 创建/删除改为 session 级别（只做一次）
2. 测试间用事务回滚隔离，不再整库重建
3. 减少顶层模型导入，按需加载
"""

from typing import AsyncGenerator
import os

os.environ.setdefault("ENVIRONMENT", "testing")

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
import pytest
import pytest_asyncio

from fastapi_backend.core.database import Base, get_db
from fastapi_backend.main import app

# ========== 数据库配置 ==========

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ========== Session 级 Schema 初始化 ==========


@pytest_asyncio.fixture(scope="session")
async def _init_db():
    """整个测试 session 只建一次表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ========== 函数级数据清理 ==========


async def _truncate_all_tables():
    """清空所有表数据但不删除表结构"""
    async with engine.begin() as conn:
        # SQLite 不支持 TRUNCATE, 用 DELETE
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture(name="db_session")
async def db_session_fixture(_init_db) -> AsyncGenerator[AsyncSession, None]:
    """每条测试前清空数据，获得独立 session"""
    await _truncate_all_tables()
    async with TestingSessionLocal() as session:
        yield session


# ========== 同步 TestClient ==========


@pytest.fixture(name="client")
def client_fixture(db_session: AsyncSession):
    """同步 HTTP 测试客户端，注入当前测试的 db_session"""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
