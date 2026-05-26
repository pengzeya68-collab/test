"""
Async SQLAlchemy database setup for fastapi_backend.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from fastapi_backend.core.config import settings


def _normalize_async_database_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return database_url


def _build_engine_kwargs(database_url: str) -> dict:
    """根据数据库类型构建引擎参数"""
    normalized = _normalize_async_database_url(database_url)
    is_sqlite = normalized.startswith("sqlite+")
    
    kwargs = {
        "echo": False,
    }
    
    if is_sqlite:
        # SQLite 只支持这些参数
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # MySQL/PostgreSQL 支持连接池参数
        kwargs.update({
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
        })
    
    return kwargs


engine = create_async_engine(
    _normalize_async_database_url(settings.DATABASE_URL),
    **_build_engine_kwargs(settings.DATABASE_URL),
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
