"""
TestMaster 习题系统全面升级脚本 V3

功能:
1. 删除所有旧习题
2. 导入全新习题（选择题 + 编程题 + 简答题）
3. 绑定到对应学习路径
4. 更新学习路径的 exercise_count

习题设计理念:
- 每道题与课程知识点精确对应
- 编程题附带 test_cases、code_template、hint
- SQL 题附带 setup_sql（建表+造数据）
- 难度梯度合理：每条路径 easy/medium/hard 均有覆盖
- 题型多样化：不是全选择题
"""

import asyncio
import sys
import os
import io

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import Exercise, LearningPath

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Import all phase data from new structure
from exercise_data.phase1_basic.software_testing_basics import EXERCISES as PHASE1_ST
from exercise_data.phase1_basic.sql_database import EXERCISES as PHASE1_SQL
from exercise_data.phase1_basic.linux_basics import EXERCISES as PHASE1_LINUX
from exercise_data.phase1_basic.python_programming import EXERCISES as PHASE1_PY
from exercise_data.phase1_basic.software_engineering import EXERCISES as PHASE1_SE

# Try to import phase 2-5 data (may not exist yet)
PHASE2_DESIGN = {}
PHASE2_DEFECT = {}
PHASE2_PLAN = {}
PHASE3_API = {}
PHASE3_SELENIUM = {}
PHASE3_PYTEST = {}
PHASE3_MOBILE = {}
PHASE4_PERF = {}
PHASE4_SECURITY = {}
PHASE4_DEVOPS = {}
PHASE4_PLATFORM = {}
PHASE5_AI = {}
PHASE5_ARCH = {}

try:
    from exercise_data.phase2_skills.test_case_design import EXERCISES as PHASE2_DESIGN
except ImportError:
    pass

try:
    from exercise_data.phase2_skills.defect_management import EXERCISES as PHASE2_DEFECT
except ImportError:
    pass

try:
    from exercise_data.phase2_skills.test_planning import EXERCISES as PHASE2_PLAN
except ImportError:
    pass

try:
    from exercise_data.phase3_automation.api_testing import EXERCISES as PHASE3_API
except ImportError:
    pass

try:
    from exercise_data.phase3_automation.selenium_ui import EXERCISES as PHASE3_SELENIUM
except ImportError:
    pass

try:
    from exercise_data.phase3_automation.requests_pytest import EXERCISES as PHASE3_PYTEST
except ImportError:
    pass

try:
    from exercise_data.phase3_automation.mobile_testing import EXERCISES as PHASE3_MOBILE
except ImportError:
    pass

try:
    from exercise_data.phase4_advanced.performance_testing import EXERCISES as PHASE4_PERF
except ImportError:
    pass

try:
    from exercise_data.phase4_advanced.security_testing import EXERCISES as PHASE4_SECURITY
except ImportError:
    pass

try:
    from exercise_data.phase4_advanced.devops_cicd import EXERCISES as PHASE4_DEVOPS
except ImportError:
    pass

try:
    from exercise_data.phase4_advanced.test_platform import EXERCISES as PHASE4_PLATFORM
except ImportError:
    pass

try:
    from exercise_data.phase5_expert.ai_testing import EXERCISES as PHASE5_AI
except ImportError:
    pass

try:
    from exercise_data.phase5_expert.test_architecture import EXERCISES as PHASE5_ARCH
except ImportError:
    pass

# Merge all exercises
ALL_EXERCISES = {}
all_phases = [
    PHASE1_ST, PHASE1_SQL, PHASE1_LINUX, PHASE1_PY, PHASE1_SE,
    PHASE2_DESIGN, PHASE2_DEFECT, PHASE2_PLAN,
    PHASE3_API, PHASE3_SELENIUM, PHASE3_PYTEST, PHASE3_MOBILE,
    PHASE4_PERF, PHASE4_SECURITY, PHASE4_DEVOPS, PHASE4_PLATFORM,
    PHASE5_AI, PHASE5_ARCH,
]

for phase in all_phases:
    for k, v in phase.items():
        if k in ALL_EXERCISES:
            ALL_EXERCISES[k].extend(v)
        else:
            ALL_EXERCISES[k] = v


async def seed_all():
    async with async_session() as session:
        print("=" * 70)
        print("[STEP 1] 统计旧习题...")
        print("=" * 70)

        result = await session.execute(text("SELECT COUNT(*) FROM exercises"))
        old_count = result.scalar()
        print(f"  旧习题总数: {old_count}")

        # Type distribution of old exercises
        result = await session.execute(
            text("SELECT exercise_type, COUNT(*) FROM exercises GROUP BY exercise_type")
        )
        for row in result.fetchall():
            print(f"    {row[0]}: {row[1]}")

        print("\n" + "=" * 70)
        print("[STEP 2] 删除旧习题...")
        print("=" * 70)
        await session.execute(delete(Exercise))
        await session.commit()
        print(f"  [OK] 已删除 {old_count} 道旧习题")

        print("\n" + "=" * 70)
        print("[STEP 3] 获取学习路径ID映射...")
        print("=" * 70)

        result = await session.execute(text("SELECT id, title FROM learning_paths"))
        path_map = {}
        for row in result.fetchall():
            path_map[row[1]] = row[0]
            print(f"  ID={row[0]} -> {row[1]}")

        missing = set(ALL_EXERCISES.keys()) - set(path_map.keys())
        if missing:
            print(f"\n  [WARN] 以下路径在数据库中不存在: {missing}")

        print("\n" + "=" * 70)
        print("[STEP 4] 批量插入新习题...")
        print("=" * 70)

        total = 0
        stats = {}
        type_stats = {}
        diff_stats = {}

        for path_title, exercises in ALL_EXERCISES.items():
            path_id = path_map.get(path_title)
            if not path_id:
                print(f"  [SKIP] 路径不存在: {path_title}")
                continue

            added = 0
            batch = []
            batch_size = 50

            # Determine if this is a SQL-related path
            is_sql_path = "SQL" in path_title or "数据库" in path_title

            # Counters for distributing types among single_choice questions
            sc_idx = 0  # counter for single_choice questions only

            for idx, ex in enumerate(exercises):
                etype = ex.get("exercise_type", "choice")
                sol = ex.get("solution", "")
                desc = ex.get("description", "")
                opts = ex.get("options", [])

                # Auto-detect multiple_choice: solution has multiple letters like "AB", "ACD"
                if etype == "single_choice" and len(sol) > 1 and sol.isalpha() and sol == sol.upper():
                    etype = "multiple_choice"

                # Distribute single_choice into multiple_choice and true_false
                if etype == "single_choice":
                    # Every 5th single_choice -> multiple_choice (20%)
                    if sc_idx % 5 == 1:
                        etype = "multiple_choice"
                    # Every 6th single_choice -> true_false (but not overlapping with mc)
                    elif sc_idx % 6 == 0 and sc_idx > 0:
                        etype = "true_false"
                    sc_idx += 1

                # For SQL path code exercises, set language to sql
                lang = ex.get("language", "中文")
                if is_sql_path and etype == "code":
                    lang = "sql"

                exercise = Exercise(
                    title=ex["title"],
                    description=desc,
                    instructions=ex.get("instructions", "请选择正确答案"),
                    solution=sol,
                    difficulty=ex.get("difficulty", "easy"),
                    language=lang,
                    module=ex.get("module", "normal"),
                    category=ex.get("category", ""),
                    stage=ex.get("stage", 1),
                    knowledge_point=ex.get("knowledge_point", ""),
                    time_estimate=ex.get("time_estimate", 3),
                    exercise_type=etype,
                    is_public=True,
                    learning_path_id=path_id,
                    test_cases=ex.get("test_cases"),
                    code_template=ex.get("code_template"),
                    expected_output=ex.get("expected_output"),
                    hint=ex.get("hint"),
                    setup_sql=ex.get("setup_sql"),
                )
                batch.append(exercise)
                session.add(exercise)
                added += 1

                # Track stats
                etype = ex.get("exercise_type", "choice")
                diff = ex.get("difficulty", "easy")
                type_stats[etype] = type_stats.get(etype, 0) + 1
                diff_stats[diff] = diff_stats.get(diff, 0) + 1

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
        print("[STEP 5] 更新学习路径习题计数...")
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
        print("[RESULT] 习题系统升级完成！")
        print("=" * 70)
        print(f"  总学习路径: {len(stats)}")
        print(f"  总习题数量: {total}")
        print(f"  平均每路径: {total // max(len(stats), 1)} 题")
        print()

        print("  题型分布:")
        for etype, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            pct = count * 100 // max(total, 1)
            bar = "█" * (count // 5)
            print(f"    {etype:12s} {bar} ({count}题, {pct}%)")

        print()
        print("  难度分布:")
        for diff, count in sorted(diff_stats.items()):
            pct = count * 100 // max(total, 1)
            bar = "█" * (count // 5)
            print(f"    {diff:12s} {bar} ({count}题, {pct}%)")

        print()
        print("  各路径题数:")
        for title, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            bar_len = min(count // 3, 40)
            bar = "█" * bar_len
            print(f"    {title:<28s} {bar} ({count}题)")

        print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("█  TestMaster 习题系统全面升级 V3")
    print("█  理念: 知识点精确对应 + 题型多样化 + 编程实战")
    print("█" * 70 + "\n")

    asyncio.run(seed_all())
