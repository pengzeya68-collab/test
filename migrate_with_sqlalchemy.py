
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi_backend.core.autotest_database import engine
from sqlalchemy import text

async def add_extractors_column():
    print("开始添加 extractors 列...")
    
    async with engine.connect() as conn:
        # 首先检查表结构
        result = await conn.execute(text("PRAGMA table_info(api_cases)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"当前 api_cases 表的列: {columns}")
        
        if 'extractors' not in columns:
            print("正在添加 extractors 列...")
            await conn.execute(text("ALTER TABLE api_cases ADD COLUMN extractors TEXT"))
            await conn.commit()
            print("extractors 列添加成功！")
        else:
            print("extractors 列已存在，无需添加")

if __name__ == "__main__":
    asyncio.run(add_extractors_column())

