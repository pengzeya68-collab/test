"""检查数据库中assert_rules的实际格式"""
import asyncio
import json
from auto_test_platform.models import ApiCase
from sqlalchemy import select
from auto_test_platform.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ApiCase).limit(5))
        cases = result.scalars().all()
        for case in cases:
            print(f"Case ID: {case.id}, name: {case.name}")
            print(f"  assert_rules type: {type(case.assert_rules)}")
            print(f"  assert_rules value: {repr(case.assert_rules)}")
            if isinstance(case.assert_rules, dict):
                print(f"  Keys: {list(case.assert_rules.keys())}")
            print()

asyncio.run(check())