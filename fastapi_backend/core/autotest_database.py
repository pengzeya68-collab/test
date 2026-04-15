"""
AutoTest 独立数据库模块

使用 instance/auto_test.db 保持数据兼容性，
通过 FastAPI 依赖注入提供 session。
"""
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

INSTANCE_DIR = Path(__file__).resolve().parent.parent.parent / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{INSTANCE_DIR}/auto_test.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 使用独立的 Base，与主数据库不共享 metadata
AutoTestBase = declarative_base()

# 便捷的 async_session 上下文管理器（供服务层使用）
async_session = AsyncSessionLocal


def check_and_add_columns(conn):
    """检查并添加缺失的列"""
    # 检查 api_cases 表是否存在 params 列
    cursor = conn.execute(text("PRAGMA table_info(api_cases)"))
    columns = [row[1] for row in cursor.fetchall()]

    if "params" not in columns:
        print("Adding params column to api_cases table...")
        try:
            conn.execute(text("ALTER TABLE api_cases ADD COLUMN params TEXT"))
            print("[OK] params column added")
        except Exception as e:
            print(f"[ERROR] adding params column: {e}")


async def get_autotest_db() -> AsyncSession:
    """AutoTest 数据库依赖注入"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_autotest_db() -> None:
    """初始化 AutoTest 数据库（创建所有表）"""
    # 导入所有模型以注册到 metadata
    import fastapi_backend.models.autotest as _  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(AutoTestBase.metadata.create_all)
        
        # 检查并添加缺失的列
        await conn.run_sync(check_and_add_columns)
