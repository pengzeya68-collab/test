"""
TestMaster 习题综合迁移脚本
1. 清理所有旧习题
2. 导入P1/P2/P3习题数据
3. 绑定所有习题到对应学习路径
4. 更新学习路径的exercise_count
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import Base, Exercise, LearningPath

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from seed_exercises_p1 import EXERCISES_1
from seed_exercises_p2 import EXERCISES_2
from seed_exercises_p3 import EXERCISES_3

ALL_EXERCISES = {}
for d in [EXERCISES_1, EXERCISES_2, EXERCISES_3]:
    for k, v in d.items():
        ALL_EXERCISES[k] = v

async def seed_all():
    async with async_session() as session:
        print("=" * 70)
        print("[STEP 1] 删除旧习题...")
        print("=" * 70)

        result = await session.execute(text("SELECT COUNT(*) FROM exercises"))
        old_count = result.scalar()
        print(f"  旧习题总数: {old_count}")
        await session.execute(delete(Exercise))
        await session.commit()
        print(f"  [OK] 已删除 {old_count} 道旧习题")

        print("\n" + "=" * 70)
        print("[STEP 2] 获取学习路径ID映射...")
        print("=" * 70)

        result = await session.execute(text("SELECT id, title FROM learning_paths"))
        path_map = {}
        for row in result.fetchall():
            path_map[row[1]] = row[0]
            print(f"  ID={row[0]} -> {row[1]}")

        missing = set(ALL_EXERCISES.keys()) - set(path_map.keys())
        if missing:
            print(f"\n  [WARN] 以下路径在数据库中不存在: {missing}")
            for m in missing:
                print(f"    - {m}")

        print("\n" + "=" * 70)
        print("[STEP 3] 批量插入习题...")
        print("=" * 70)

        total = 0
        stats = {}

        for path_title, exercises in ALL_EXERCISES.items():
            path_id = path_map.get(path_title)
            if not path_id:
                print(f"  [SKIP] 路径不存在: {path_title}")
                continue

            added = 0
            batch = []
            batch_size = 50

            for ex in exercises:
                exercise = Exercise(
                    title=ex["title"],
                    description=ex.get("description", ""),
                    instructions=ex.get("instructions", "请选择正确答案"),
                    solution=ex["solution"],
                    difficulty=ex.get("difficulty", "beginner"),
                    language=ex.get("language", "中文"),
                    module=ex.get("module", "normal"),
                    category=ex.get("category", ""),
                    stage=ex.get("stage", 1),
                    knowledge_point=ex.get("knowledge_point", ""),
                    time_estimate=ex.get("time_estimate", 1),
                    exercise_type=ex.get("exercise_type", "choice"),
                    is_public=True,
                    learning_path_id=path_id,
                )
                batch.append(exercise)
                session.add(exercise)
                added += 1

                if len(batch) >= batch_size:
                    await session.flush()
                    batch = []

            if batch:
                await session.flush()

            total += added
            stats[path_title] = added
            print(f"  [OK] {path_title:30s} +{added}题")

        await session.commit()
        print(f"\n  总计插入: {total} 道习题")

        print("\n" + "=" * 70)
        print("[STEP 4] 更新学习路径习题计数...")
        print("=" * 70)

        for path_title, count in stats.items():
            path_id = path_map.get(path_title)
            if path_id:
                await session.execute(
                    update(LearningPath)
                    .where(LearningPath.id == path_id)
                    .values(exercise_count=count)
                )
                print(f"  {path_title:30s} exercise_count = {count}")

        await session.commit()
        print("  [OK] 所有学习路径习题计数已更新")

        print("\n" + "=" * 70)
        print("[RESULT] 习题迁移完成！")
        print("=" * 70)
        print(f"  总学习路径: {len(stats)}")
        print(f"  总习题数量: {total}")
        print(f"  平均每路径: {total // len(stats)} 题")
        print()

        for title, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            bar_len = min(count // 5, 30)
            bar = "\u2588" * bar_len
            print(f"  {title:<28s} {bar} ({count}题)")

        print("=" * 70)

    await engine.dispose()

if __name__ == "__main__":
    print("\n" + "\u2588" * 70)
    print("\u2588  TestMaster 习题综合迁移脚本")
    print("\u2588  功能: 清旧题 -> 导新题 -> 绑路径 -> 更计数")
    print("\u2588" * 70 + "\n")

    asyncio.run(seed_all())