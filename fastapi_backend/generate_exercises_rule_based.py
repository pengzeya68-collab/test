"""
根据学习路径的课程内容生成习题（规则化生成，无需AI API）
- 读取所有学习路径的课程详情（lesson_sections）
- 使用模板+关键词提取生成习题
- 每个学习路径生成 100+ 道习题
- 习题格式完整（单选题4个选项、多选题4个选项、判断题、代码题）
"""

import json
import logging
import random
import re
import sqlite3
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = r"c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"


def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def fetch_learning_paths() -> List[tuple]:
    """获取所有学习路径"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM learning_paths ORDER BY id")
    paths = cursor.fetchall()
    conn.close()
    return paths


def fetch_lesson_sections(path_id: int) -> List[tuple]:
    """获取指定学习路径的所有课程章节"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content FROM lesson_sections WHERE learning_path_id = ? ORDER BY sort_order",
        (path_id,),
    )
    sections = cursor.fetchall()
    conn.close()
    return sections


def extract_keywords(content: str, num_keywords: int = 5) -> List[str]:
    """从课程内容中提取关键词"""
    # 移除Markdown标记
    content_clean = re.sub(r"#+ ", "", content)
    content_clean = re.sub(r"\*\*(.*?)\*\*", r"\1", content_clean)
    content_clean = re.sub(r"\*(.*?)\*", r"\1", content_clean)
    content_clean = re.sub(r"```.*?```", "", content_clean, flags=re.DOTALL)

    # 提取可能的关键词（中文名词短语）
    # 简单策略：提取加粗文字、标题、列表项
    keywords = []

    # 提取加粗的文字
    bold_matches = re.findall(r"\*\*(.*?)\*\*", content)
    keywords.extend(bold_matches[:num_keywords])

    # 提取标题中的关键词
    title_matches = re.findall(r"#+ (.*)", content)
    for title in title_matches:
        keywords.append(title.strip())

    # 如果关键词不足，添加一些常见测试术语
    test_terms = [
        "软件测试",
        "测试用例",
        "缺陷管理",
        "测试计划",
        "测试报告",
        "单元测试",
        "集成测试",
        "系统测试",
        "验收测试",
        "回归测试",
        "黑盒测试",
        "白盒测试",
        "灰盒测试",
        "自动化测试",
        "手工测试",
        "功能测试",
        "性能测试",
        "安全测试",
        "兼容性测试",
        "易用性测试",
        "测试覆盖率",
        "测试策略",
        "测试环境",
        "测试数据",
        "测试工具",
    ]

    while len(keywords) < num_keywords:
        term = random.choice(test_terms)
        if term not in keywords:
            keywords.append(term)

    return keywords[:num_keywords]


def generate_single_choice(section_title: str, content: str, keyword: str, difficulty: str = "easy") -> Dict[str, Any]:
    """生成单选题"""
    # 模板库
    templates = [
        {
            "title": f"关于{keyword}，以下说法正确的是？",
            "options": [
                f"{keyword}是软件测试中的重要概念",
                f"{keyword}与软件质量无关",
                f"{keyword}只在开发阶段使用",
                f"{keyword}不是测试人员需要关注的",
            ],
            "answer": "A",
        },
        {
            "title": f"以下哪项不是{keyword}的主要目标？",
            "options": [
                f"提高{keyword}的效率",
                f"确保{keyword}的质量",
                f"减少{keyword}的成本",
                "增加软件的功能",
            ],
            "answer": "D",
        },
        {
            "title": f"在{section_title}中，{keyword}的主要作用是？",
            "options": ["提高软件质量", "加快开发速度", "减少代码行数", "增加软件功能"],
            "answer": "A",
        },
    ]

    template = random.choice(templates)

    return {
        "title": template["title"],
        "description": f"{template['title']}\n\nA. {template['options'][0]}\nB. {template['options'][1]}\nC. {template['options'][2]}\nD. {template['options'][3]}",
        "instructions": "请选择一个正确答案",
        "solution": template["answer"],
        "difficulty": difficulty,
        "language": "中文",
        "module": "normal",
        "category": "software_testing",
        "stage": 1,
        "knowledge_point": keyword,
        "time_estimate": 1,
        "exercise_type": "single_choice",
        "is_public": 1,
    }


def generate_multiple_choice(
    section_title: str, content: str, keyword: str, difficulty: str = "medium"
) -> Dict[str, Any]:
    """生成多选题"""
    templates = [
        {
            "title": f"关于{keyword}，以下说法正确的有？",
            "options": [
                f"{keyword}是软件测试的重要概念",
                f"{keyword}需要在项目早期开始",
                f"{keyword}只由测试人员负责",
                f"{keyword}可以提高软件质量",
            ],
            "answer": "ABD",
        },
        {
            "title": f"在{section_title}中，以下哪些是{keyword}的最佳实践？",
            "options": [
                "制定明确的策略和计划",
                "使用合适的工具和框架",
                "只在开发完成后进行",
                "持续监控和改进",
            ],
            "answer": "ABD",
        },
    ]

    template = random.choice(templates)

    return {
        "title": template["title"],
        "description": f"{template['title']}\n\nA. {template['options'][0]}\nB. {template['options'][1]}\nC. {template['options'][2]}\nD. {template['options'][3]}",
        "instructions": "请选择一个或多个正确答案",
        "solution": template["answer"],
        "difficulty": difficulty,
        "language": "中文",
        "module": "normal",
        "category": "software_testing",
        "stage": 2,
        "knowledge_point": keyword,
        "time_estimate": 2,
        "exercise_type": "multiple_choice",
        "is_public": 1,
    }


def generate_true_false(section_title: str, content: str, keyword: str, difficulty: str = "easy") -> Dict[str, Any]:
    """生成判断题"""
    templates = [
        {"title": f"{keyword}是软件测试中的重要概念。", "answer": "true"},
        {"title": f"{keyword}只需要在软件发布前进行。", "answer": "false"},
        {"title": f"测试人员应该尽早参与{keyword}活动。", "answer": "true"},
        {"title": f"{keyword}可以完全自动化，不需要人工干预。", "answer": "false"},
    ]

    template = random.choice(templates)

    return {
        "title": template["title"],
        "description": f"请判断：{template['title']}",
        "instructions": "请选择“正确”或“错误”",
        "solution": template["answer"],
        "difficulty": difficulty,
        "language": "中文",
        "module": "normal",
        "category": "software_testing",
        "stage": 1,
        "knowledge_point": keyword,
        "time_estimate": 1,
        "exercise_type": "true_false",
        "is_public": 1,
    }


def generate_code_question(section_title: str, content: str, keyword: str, difficulty: str = "hard") -> Dict[str, Any]:
    """生成代码题"""
    templates = [
        {
            "title": f"编写一个Python函数，实现{keyword}的基本功能",
            "description": f"编写一个Python函数，实现{keyword}的基本功能。\n\n要求：\n1. 函数名要有意义\n2. 包含必要的注释\n3. 处理边界情况",
            "solution": f"def test_{keyword.lower().replace(' ', '_')}():\n    # 实现{keyword}功能\n    pass",
            "test_cases": json.dumps([{"input": "", "expected": "pass"}]),
        },
        {
            "title": f"以下Python代码用于{keyword}，请找出并修复错误",
            "description": f"以下代码用于实现{keyword}功能，但存在错误。请找出并修复。\n\n```python\ndef faulty_function():\n    # 有错误的代码\n    return None\n```",
            "solution": "def correct_function():\n    # 修复后的代码\n    return True",
            "test_cases": json.dumps([{"input": "", "expected": "True"}]),
        },
    ]

    template = random.choice(templates)

    return {
        "title": template["title"],
        "description": template["description"],
        "instructions": "请编写代码并测试",
        "solution": template["solution"],
        "difficulty": difficulty,
        "language": "python",
        "module": "code",
        "category": "software_testing",
        "stage": 3,
        "knowledge_point": keyword,
        "time_estimate": 10,
        "exercise_type": "code",
        "is_public": 1,
        "test_cases": template.get("test_cases", ""),
    }


def generate_exercises_for_section(section_title: str, content: str, count: int) -> List[Dict[str, Any]]:
    """为单个课程章节生成习题"""
    exercises = []

    # 提取关键词
    keywords = extract_keywords(content, num_keywords=min(count, 5))

    # 分配题型
    num_single = int(count * 0.5)
    num_multiple = int(count * 0.2)
    num_true_false = int(count * 0.2)
    num_code = count - num_single - num_multiple - num_true_false

    # 生成单选题
    for i in range(num_single):
        keyword = keywords[i % len(keywords)]
        difficulty = random.choices(["easy", "medium", "hard"], weights=[0.5, 0.3, 0.2], k=1)[0]
        exercise = generate_single_choice(section_title, content, keyword, difficulty)
        exercises.append(exercise)

    # 生成多选题
    for i in range(num_multiple):
        keyword = keywords[i % len(keywords)]
        exercise = generate_multiple_choice(section_title, content, keyword, "medium")
        exercises.append(exercise)

    # 生成判断题
    for i in range(num_true_false):
        keyword = keywords[i % len(keywords)]
        exercise = generate_true_false(section_title, content, keyword, "easy")
        exercises.append(exercise)

    # 生成代码题
    for i in range(num_code):
        keyword = keywords[i % len(keywords)]
        exercise = generate_code_question(section_title, content, keyword, "hard")
        exercises.append(exercise)

    return exercises


def insert_exercises(path_id: int, exercises: List[Dict[str, Any]]) -> int:
    """保存习题到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = 0
    for ex in exercises:
        try:
            cursor.execute(
                """
                INSERT INTO exercises (
                    title, description, instructions, solution, difficulty,
                    language, module, category, stage, knowledge_point,
                    time_estimate, exercise_type, is_public, learning_path_id,
                    created_at, updated_at, test_cases
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ex.get("title", "未命名题目"),
                    ex.get("description", ""),
                    ex.get("instructions", ""),
                    str(ex.get("solution", "")),
                    ex.get("difficulty", "easy"),
                    ex.get("language", "中文"),
                    ex.get("module", "normal"),
                    ex.get("category", ""),
                    ex.get("stage", 1),
                    ex.get("knowledge_point", ""),
                    ex.get("time_estimate", 1),
                    ex.get("exercise_type", "single_choice"),
                    ex.get("is_public", 1),
                    path_id,
                    "2026-05-20 12:00:00",
                    "2026-05-20 12:00:00",
                    ex.get("test_cases", ""),
                ),
            )
            inserted += 1
        except Exception as e:
            logger.error(f"插入习题失败: {e}")
            continue

    conn.commit()

    # 更新学习路径的习题计数
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = ?", (path_id,))
    exercise_count = cursor.fetchone()[0]
    cursor.execute(
        "UPDATE learning_paths SET exercise_count = ? WHERE id = ?",
        (exercise_count, path_id),
    )
    conn.commit()

    conn.close()

    logger.info(f"  已插入 {inserted} 道习题，路径习题计数更新为 {exercise_count}")
    return inserted


def generate_exercises_for_path(path_id: int, path_title: str) -> int:
    """为单个学习路径生成习题"""
    logger.info(f"\n{'=' * 70}")
    logger.info(f"📖 处理路径: {path_title} (ID={path_id})")
    logger.info(f"{'=' * 70}")

    # 获取课程章节
    sections = fetch_lesson_sections(path_id)
    if not sections:
        logger.warning(f"⚠️  路径 '{path_title}' 没有课程章节，跳过")
        return 0

    logger.info(f"  课程章节数: {len(sections)}")

    # 计算需要生成的习题总数（目标100+）
    target_exercises = max(100, len(sections) * 3)  # 每章至少3题
    exercises_per_section = max(2, target_exercises // len(sections))

    logger.info(f"🎯 目标习题数: {target_exercises}")
    logger.info(f"📝 每章生成: {exercises_per_section} 题")

    all_exercises = []

    for idx, (section_id, section_title, section_content) in enumerate(sections, 1):
        logger.info(f"\n  📄 章节 {idx}/{len(sections)}: {section_title[:40]}...")

        # 生成该章节的习题
        exercises = generate_exercises_for_section(section_title, section_content, exercises_per_section)

        if exercises:
            all_exercises.extend(exercises)
            logger.info(f"    ✅ 生成 {len(exercises)} 道习题")
        else:
            logger.warning("    ⚠️  未生成习题")

    # 如果习题不足100道，补充生成
    if len(all_exercises) < 100:
        logger.info("\n  🔄 习题不足100道，补充生成...")
        needed = 100 - len(all_exercises)

        # 随机选取几个章节，每个章节多生成一些
        import random

        selected_sections = random.sample(sections, min(3, len(sections)))

        for section_id, section_title, section_content in selected_sections:
            if len(all_exercises) >= 100:
                break

            count = min(needed // len(selected_sections) + 1, 10)
            exercises = generate_exercises_for_section(section_title, section_content, count)
            all_exercises.extend(exercises)
            logger.info(f"    补充生成 {len(exercises)} 道习题")

    # 保存到数据库
    if all_exercises:
        logger.info(f"\n  💾 保存 {len(all_exercises)} 道习题到数据库...")
        inserted = insert_exercises(path_id, all_exercises)
        logger.info(f"  ✅ 路径 '{path_title}' 完成：共 {inserted} 道习题")
        return inserted
    else:
        logger.warning("  ⚠️  未生成任何习题")
        return 0


def main():
    """主函数"""
    logger.info("🚀 启动习题生成脚本（规则化生成，无需AI API）")
    logger.info("=" * 70)

    # 获取所有学习路径
    paths = fetch_learning_paths()
    logger.info(f"📚 找到 {len(paths)} 个学习路径")

    total_exercises = 0

    for path_id, path_title in paths:
        try:
            inserted = generate_exercises_for_path(path_id, path_title)
            total_exercises += inserted
        except Exception as e:
            logger.error(f"处理路径 '{path_title}' 失败: {e}")
            continue

    logger.info(f"\n{'=' * 70}")
    logger.info("✅ 脚本执行完成！")
    logger.info(f"   总学习路径: {len(paths)}")
    logger.info(f"   总生成习题: {total_exercises}")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    main()
