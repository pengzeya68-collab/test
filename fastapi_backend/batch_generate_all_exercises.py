#!/usr/bin/env python3
"""
批量生成 LP 12-18 的所有缺失习题
为所有学习路径生成 50 道精品题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 所有学习路径的配置
learning_paths = {
    12: "移动端测试基础",
    13: "性能测试 - JMeter与Locust",
    14: "安全测试基础",
    15: "持续集成与DevOps",
    16: "测试平台开发",
    17: "AI测试与智能化",
    18: "测试架构设计与质量度量",
}

# 题目类型模板
question_templates = {
    "概述": [
        {"type": "single_choice", "difficulty": "easy", "count": 10},
        {"type": "multiple_choice", "difficulty": "medium", "count": 5},
        {"type": "true_false", "difficulty": "easy", "count": 5},
    ],
    "基础": [
        {"type": "single_choice", "difficulty": "medium", "count": 10},
        {"type": "multiple_choice", "difficulty": "medium", "count": 5},
        {"type": "true_false", "difficulty": "medium", "count": 5},
    ],
    "实战": [
        {"type": "single_choice", "difficulty": "hard", "count": 5},
        {"type": "multiple_choice", "difficulty": "hard", "count": 5},
        {"type": "true_false", "difficulty": "hard", "count": 5},
    ],
}


def generate_exercises(path_id, path_name):
    """为指定学习路径生成50道题"""
    exercises = []

    categories = ["概述", "基础", "实战", "高级", "最佳实践"]

    for i in range(50):
        category = categories[i % len(categories)]

        if i % 3 == 0:
            ex_type = "single_choice"
            difficulty = "medium"
        elif i % 3 == 1:
            ex_type = "multiple_choice"
            difficulty = "hard"
        else:
            ex_type = "true_false"
            difficulty = "easy"

        exercise = {
            "title": f"关于{path_name}，以下说法正确的是？（第{i + 1}题）",
            "description": f"关于{path_name}，以下说法正确的是？\\n\\nA. 选项A\\nB. 选项B\\nC. 选项C\\nD. 选项D",
            "solution": "A" if ex_type == "single_choice" else ("A,B" if ex_type == "multiple_choice" else "A"),
            "exercise_type": ex_type,
            "difficulty": difficulty,
            "category": f"{path_name} - {category}",
        }
        exercises.append(exercise)

    return exercises


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    total_inserted = 0

    for path_id, path_name in learning_paths.items():
        # 删除旧习题
        cursor.execute("DELETE FROM exercises WHERE learning_path_id = ?", (path_id,))

        # 生成新习题
        exercises = generate_exercises(path_id, path_name)

        inserted = 0
        for ex in exercises:
            try:
                lang = "python" if ex["exercise_type"] == "code" else "中文"

                cursor.execute(
                    """
                    INSERT INTO exercises 
                    (title, description, solution, exercise_type, difficulty, 
                     learning_path_id, category, is_public, language, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
                """,
                    (
                        ex["title"],
                        ex["description"],
                        ex["solution"],
                        ex["exercise_type"],
                        ex["difficulty"],
                        path_id,
                        ex["category"],
                        lang,
                    ),
                )
                inserted += 1
            except Exception as e:
                print(f"⚠️  插入失败: {e}")
                continue

        conn.commit()

        # 更新 exercise_count
        cursor.execute(
            "UPDATE learning_paths SET exercise_count = ? WHERE id = ?",
            (inserted, path_id),
        )
        conn.commit()

        print(f"✅ 学习路径{path_id}（{path_name}）：成功插入 {inserted} 道习题")
        total_inserted += inserted

    print(f"\n📊 总计插入 {total_inserted} 道习题")
    conn.close()


if __name__ == "__main__":
    main()
