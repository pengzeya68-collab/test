import asyncio
from database import async_session
from models import TestScenario, Environment
from sqlalchemy import select

async def main():
    async with async_session() as s:
        result = await s.execute(select(TestScenario).limit(5))
        scenarios = result.scalars().all()
        print("=== 场景列表 ===")
        for s in scenarios:
            print(f"场景: id={s.id}, name={s.name}, env_id={s.env_id}")

        print("\n=== 环境列表 ===")
        env_result = await s.execute(select(Environment).limit(5))
        envs = env_result.scalars().all()
        for e in envs:
            print(f"环境: id={e.id}, name={e.name}, base_url={e.base_url}")

asyncio.run(main())