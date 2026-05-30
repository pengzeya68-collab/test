"""
根据学习路径的课程内容生成习题（简化版）
- 直接连接SQLite数据库
- 使用requests调用MiniMax AI
- 每个学习路径生成100+道习题
"""

import json
import logging
import random
import re
import sqlite3
import time

import requests

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = r"c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"

# MiniMax AI 配置
MINIMAX_API_KEY = "sk-cp-PnF3Dqm0wyuV0fd3WL043-IxN00Wuk0H1wvfb_j8-g3BnXbq-CCMSI5SFtZXYfCb7b7qtv4zdvkJtRUGtZLd2QGE2L0CyAbSRk4zQ4F6rkjgpTx-kX9fgI"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-M2.7"
MINIMAX_GROUP_ID = "test_group"


def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def fetch_learning_paths() -> list:
    """获取所有学习路径"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM learning_paths ORDER BY id")
    paths = cursor.fetchall()
    conn.close()
    return paths


def fetch_lesson_sections(path_id: int) -> list:
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


def call_minimax_api(prompt: str) -> str:
    """调用MiniMax API生成习题"""
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000,
        "group_id": MINIMAX_GROUP_ID,
    }

    try:
        response = requests.post(
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"API调用失败: {e}")
        raise


def build_prompt(content: str, count: int) -> str:
    """构建AI生成习题的Prompt"""
    # 截断过长的内容
    max_content_length = 3000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[内容已截断...]"

    prompt = f"""你是一个专业的软件测试教育专家。请根据以下课程内容，生成 {count} 道高质量的练习题。

## 课程内容：
{content}

## 要求：
1. 习题必须紧密围绕课程内容，考察重点知识点
2. 题型分配（共{count}题）：
   - 单选题：{int(count * 0.5)}题（必须包含4个选项，格式：A. 选项内容）
   - 多选题：{int(count * 0.2)}题（必须包含4个选项，A/B/C/D）
   - 判断题：{int(count * 0.2)}题
   - 代码题：{int(count * 0.1)}题（如有代码相关内容）
3. 难度分布：简单50%、中等30%、困难20%
4. 每道题必须包含：
   - title: 题目名称（简洁明了）
   - description: 题目描述（单选题/多选题必须包含完整选项，如"A. 选项A\\nB. 选项B\\nC. 选项C\\nD. 选项D"）
   - solution: 正确答案（单选题:A/B/C/D，多选题:AB/ACD等，判断题:true/false）
   - difficulty: 难度（easy/medium/hard）
   - exercise_type: 题型（single_choice/multiple_choice/true_false/code）
   - knowledge_point: 知识点

## 输出格式（严格JSON数组）：
```json
[
  {{
    "title": "题目名称",
    "description": "题目描述\\n\\nA. 选项A\\nB. 选项B\\nC. 选项C\\nD. 选项D",
    "solution": "A",
    "difficulty": "easy",
    "exercise_type": "single_choice",
    "knowledge_point": "知识点名称"
  }}
]
```

## 重要：
- 选项必须完整且有区分度，不能有明显错误选项
- 正确答案必须准确，与课程内容一致
- 题目描述中要包含完整选项（A/B/C/D格式）
- 只返回JSON数组，不要其他解释文字
"""
    return prompt


def parse_ai_response(response: str) -> list:
    """解析AI返回的习题数据"""
    try:
        # 提取JSON（可能包含在```json ```中）
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            response = json_match.group(1)

        # 尝试直接解析
        exercises = json.loads(response)

        if not isinstance(exercises, list):
            raise ValueError("AI返回的不是数组格式")

        return exercises

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.error(f"Response: {response[:200]}...")
        return []


def insert_exercises(path_id: int, exercises: list):
    """保存习题到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 先删除该路径的旧习题（可选，注释掉则保留旧习题）
    # cursor.execute("DELETE FROM exercises WHERE learning_path_id = ?", (path_id,))
    # logger.info(f"已删除路径 {path_id} 的旧习题")

    inserted = 0
    for ex in exercises:
        try:
            # 验证必填字段
            if not ex.get("title") or not ex.get("solution"):
                continue

            # 确保选项格式正确（选择题）
            description = ex.get("description", "")
            if ex.get("exercise_type") in ("single_choice", "multiple_choice"):
                if "A." not in description and "A、" not in description:
                    # 如果没有选项，添加默认选项
                    description = description + "\n\nA. 选项A\nB. 选项B\nC. 选项C\nD. 选项D"

            cursor.execute(
                """
                INSERT INTO exercises (
                    title, description, instructions, solution, difficulty,
                    language, module, category, stage, knowledge_point,
                    time_estimate, exercise_type, is_public, learning_path_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ex.get("title", "未命名题目"),
                    description,
                    ex.get("instructions", "请选择正确答案"),
                    str(ex.get("solution", "")),
                    ex.get("difficulty", "easy"),
                    ex.get("language", "中文"),
                    ex.get("module", "normal"),
                    ex.get("category", ""),
                    ex.get("stage", 1),
                    ex.get("knowledge_point", ""),
                    ex.get("time_estimate", 1),
                    ex.get("exercise_type", "single_choice"),
                    1,  # is_public
                    path_id,
                    "2026-05-20 12:00:00",
                    "2026-05-20 12:00:00",
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


def generate_exercises_for_path(path_id: int, path_title: str):
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
        prompt = build_prompt(section_content, exercises_per_section)

        try:
            response = call_minimax_api(prompt)
            exercises = parse_ai_response(response)

            if exercises:
                all_exercises.extend(exercises)
                logger.info(f"    ✅ 生成 {len(exercises)} 道习题")
            else:
                logger.warning("    ⚠️  未生成习题")

            # 避免API限流
            time.sleep(1)

        except Exception as e:
            logger.error(f"    ❌ 生成失败: {e}")
            continue

    # 如果习题不足100道，补充生成
    if len(all_exercises) < 100:
        logger.info("\n  🔄 习题不足100道，补充生成...")
        needed = 100 - len(all_exercises)

        # 随机选取几个章节，每个章节多生成一些
        selected_sections = random.sample(sections, min(3, len(sections)))

        for section_id, section_title, section_content in selected_sections:
            if len(all_exercises) >= 100:
                break

            count = min(needed // len(selected_sections) + 1, 10)
            prompt = build_prompt(section_content, count)

            try:
                response = call_minimax_api(prompt)
                exercises = parse_ai_response(response)
                all_exercises.extend(exercises)
                logger.info(f"    补充生成 {len(exercises)} 道习题")
                time.sleep(1)
            except Exception as e:
                logger.error(f"    补充生成失败: {e}")
                continue

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
    logger.info("🚀 启动习题生成脚本")
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
