"""
Initialize database tables for TestMaster.
"""
import asyncio
import sys
sys.path.insert(0, r'c:\Users\lenovo\Desktop\TestMasterProject')

from fastapi_backend.core.database import engine, Base
from fastapi_backend.models.models import User, ApiGroup, ApiCase

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
