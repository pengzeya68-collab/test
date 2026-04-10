"""
数据库连接 - 异步 SQLAlchemy
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 创建异步引擎（硬编码异步驱动，不受 .env 同步配置影响）
engine = create_async_engine(
    "sqlite+aiosqlite:///./instance/testmaster.db",
    echo=False,
    connect_args={"check_same_thread": False}  # SQLite 特定配置
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 基础模型类
Base = declarative_base()

# 数据库依赖注入
async def get_db() -> AsyncSession:
    """获取数据库会话依赖"""
    async with AsyncSessionLocal() as session:
        yield session
