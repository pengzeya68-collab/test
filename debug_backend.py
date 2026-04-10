import sys
import os
sys.path.append('c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform')

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session
from models import ApiCase

async def debug_query():
    async with async_session() as session:
        # 测试查询
        query = select(ApiCase)
        print('Query created')
        
        # 模拟搜索
        search = ''
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    ApiCase.name.like(search_pattern),
                    ApiCase.url.like(search_pattern)
                )
            )
        
        # 计数
        count_query = select(func.count()).select_from(query.subquery())
        print('Count query created')
        
        try:
            total = (await session.execute(count_query)).scalar()
            print(f'Total count: {total}')
        except Exception as e:
            print(f'Count error: {e}')
            import traceback
            traceback.print_exc()
            return
        
        # 获取数据
        query = query.order_by(ApiCase.id.desc())
        query = query.offset(0).limit(20)
        
        try:
            result = await session.execute(query)
            print('Query executed')
            cases = result.scalars().all()
            print(f'Got {len(cases)} cases')
            for i, case in enumerate(cases[:3]):
                print(f'  {i+1}: {case.name} - {case.method} {case.url}')
        except Exception as e:
            print(f'Data error: {e}')
            import traceback
            traceback.print_exc()

import asyncio
asyncio.run(debug_query())
