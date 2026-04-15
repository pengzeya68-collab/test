#!/usr/bin/env python3
"""
将现有题目的test_cases JSON字段迁移到TestCase表
用法: python -m scripts.migrate_test_cases
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi_backend.core.config import settings
from fastapi_backend.core.database import Base, get_db
from fastapi_backend.models.models import InterviewQuestion, TestCase


async def migrate_test_cases():
    """迁移测试用例数据"""
    # 创建数据库引擎
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with AsyncSession(engine) as session:
        try:
            # 获取所有题目
            result = await session.execute(select(InterviewQuestion))
            questions = result.scalars().all()

            total_migrated = 0
            total_skipped = 0

            for question in questions:
                # 检查是否已有测试用例记录
                test_case_result = await session.execute(
                    select(TestCase).where(TestCase.question_id == question.id)
                )
                existing_test_cases = test_case_result.scalars().all()

                if existing_test_cases:
                    print(f"题目 #{question.id} '{question.title}' 已有 {len(existing_test_cases)} 个测试用例，跳过")
                    total_skipped += 1
                    continue

                # 解析JSON测试用例
                if not question.test_cases or question.test_cases.strip() == "":
                    print(f"题目 #{question.id} '{question.title}' 没有测试用例数据，跳过")
                    total_skipped += 1
                    continue

                try:
                    test_cases_json = json.loads(question.test_cases)
                    if not isinstance(test_cases_json, list):
                        print(f"题目 #{question.id} '{question.title}' 测试用例不是列表格式，跳过")
                        total_skipped += 1
                        continue

                    # 创建TestCase记录
                    created_count = 0
                    for i, test_case in enumerate(test_cases_json):
                        if not isinstance(test_case, dict):
                            print(f"题目 #{question.id} 第{i+1}个测试用例不是字典格式，跳过")
                            continue

                        input_data = test_case.get("input", "")
                        expected_output = test_case.get("output", "")

                        # 如果output字段不存在，尝试其他可能的键
                        if expected_output == "":
                            expected_output = test_case.get("expected_output", "")

                        # 创建TestCase记录
                        new_test_case = TestCase(
                            question_id=question.id,
                            input=str(input_data),
                            expected_output=str(expected_output),
                            is_example=False,  # 默认为非示例用例
                            is_hidden=False,   # 默认为非隐藏用例
                            description=f"从JSON迁移的测试用例 #{i+1}"
                        )
                        session.add(new_test_case)
                        created_count += 1

                    if created_count > 0:
                        await session.commit()
                        print(f"题目 #{question.id} '{question.title}' 迁移了 {created_count} 个测试用例")
                        total_migrated += 1
                    else:
                        print(f"题目 #{question.id} '{question.title}' 没有有效的测试用例，跳过")
                        total_skipped += 1

                except json.JSONDecodeError as e:
                    print(f"题目 #{question.id} '{question.title}' JSON解析失败: {e}")
                    total_skipped += 1
                    continue
                except Exception as e:
                    print(f"题目 #{question.id} '{question.title}' 迁移失败: {e}")
                    await session.rollback()
                    total_skipped += 1
                    continue

            print(f"\n迁移完成!")
            print(f"成功迁移: {total_migrated} 个题目")
            print(f"跳过: {total_skipped} 个题目")

        except Exception as e:
            print(f"迁移过程中发生错误: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate_test_cases())