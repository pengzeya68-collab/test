import asyncio
import sys
sys.path.insert(0, r"C:\Users\lenovo\Desktop\TestMasterProject")
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup
from fastapi_backend.core.autotest_database import DATABASE_URL, init_autotest_db

async def test():
    # Drop existing tables and recreate with new schema
    from fastapi_backend.core.autotest_database import engine, AutoTestBase
    async with engine.begin() as conn:
        await conn.run_sync(AutoTestBase.metadata.drop_all)
    await init_autotest_db()
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 创建一个分组
        group = AutoTestGroup(name="TestGroup")
        db.add(group)
        await db.commit()
        await db.refresh(group)
        group_id = group.id

        # 创建用例，带 extractors
        case = AutoTestCase(
            group_id=group_id,
            name="TestExtractors",
            method="GET",
            url="http://example.com",
            extractors=[
                {"variableName": "token", "extractorType": "jsonpath", "expression": "$.token"}
            ],
            assert_rules=[]
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)
        case_id = case.id

        # 查询用例，检查 extractors
        from sqlalchemy import select
        result = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
        fetched = result.scalar_one()
        print("Saved extractors:", case.extractors)
        print("Fetched extractors:", fetched.extractors)

        # 更新用例，去掉 extractors
        case.extractors = []
        await db.commit()
        await db.refresh(case)

        result2 = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
        fetched2 = result2.scalar_one()
        print("After update (empty):", fetched2.extractors)

        # 清理
        await db.delete(case)
        await db.delete(group)
        await db.commit()

    await engine.dispose()
    print("Test done.")

if __name__ == "__main__":
    asyncio.run(test())