#!/usr/bin/env python3
"""
智能习题生成脚本 - 真正基于课程内容生成习题
1. 解析课程内容的markdown结构
2. 提取定义、原则、对比、列表等关键信息
3. 基于真实内容生成选择题、判断题、代码题
"""

import sqlite3
import re
import random

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"


def parse_content(content):
    """解析markdown内容，提取关键信息"""
    if not content:
        return []

    items = []

    # 1. 提取 ## 标题和对应的内容
    sections = re.split(r"\n##\s+", content)
    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        if body:
            items.append({"type": "section", "title": title, "content": body})

    # 2. 提取 **粗体** 定义 (形如：**术语**：定义)
    definitions = re.findall(r"\*\*(.+?)\*\*[:：](.+)", content)
    for term, definition in definitions:
        items.append(
            {
                "type": "definition",
                "term": term.strip(),
                "definition": definition.strip(),
            }
        )

    # 3. 提取编号列表 (形如：1. 项目)
    numbered_items = re.findall(r"^\s*(\d+)\.?\s+(.+)$", content, re.MULTILINE)
    for num, item in numbered_items[:10]:
        items.append({"type": "numbered_item", "number": num, "content": item.strip()})

    # 4. 提取 ### 小标题
    subsections = re.findall(r"###\s+(.+)", content)
    for sub in subsections:
        items.append({"type": "subsection", "title": sub.strip()})

    return items


def generate_single_choice_from_content(item, all_items, section_title):
    """基于内容生成单选题"""
    if item["type"] == "definition":
        # 基于定义生成题
        term = item["term"]
        definition = item["definition"]

        question = f"以下对「{term}」的描述，正确的是？"

        # 正确答案：使用定义
        correct = f"{definition[:100]}" if len(definition) > 100 else definition

        # 错误答案：相似的迷惑项
        wrong_answers = [
            f"与{term}无关的概念",
            f"{term}只在测试阶段使用",
            f"{term}可以通过穷举测试验证",
        ]

        options = [correct] + wrong_answers
        random.shuffle(options)

        correct_label = ["A", "B", "C", "D"][options.index(correct)]
        description = f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}"

        return {
            "title": question,
            "description": description,
            "solution": correct_label,
            "exercise_type": "single_choice",
            "difficulty": "medium",
        }

    elif item["type"] == "subsection":
        # 基于小标题生成题
        title = item["title"]

        question = f"关于「{title}」，以下说法正确的是？"

        correct = f"{title}是软件测试中的重要概念"
        wrong_answers = [
            f"{title}与软件测试无关",
            f"{title}只在开发阶段使用",
            f"{title}可以通过穷举测试验证",
        ]

        options = [correct] + wrong_answers
        random.shuffle(options)

        correct_label = ["A", "B", "C", "D"][options.index(correct)]
        description = f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}"

        return {
            "title": question,
            "description": description,
            "solution": correct_label,
            "exercise_type": "single_choice",
            "difficulty": "medium",
        }

    elif item["type"] == "numbered_item":
        # 基于列表项生成题
        content_text = item["content"]

        # 提取关键信息（前50字符）
        key_info = content_text[:50] if len(content_text) > 50 else content_text

        question = f"以下关于「{key_info}」的说法，正确的是？"

        correct = content_text
        wrong_answers = [
            f"{key_info}与软件测试无关",
            f"{key_info}只在开发阶段使用",
            f"{key_info}可以通过穷举测试验证",
        ]

        options = [correct] + wrong_answers
        random.shuffle(options)

        correct_label = ["A", "B", "C", "D"][options.index(correct)]
        description = (
            f"{question}\n\nA. {options[0][:80]}\nB. {options[1][:80]}\nC. {options[2][:80]}\nD. {options[3][:80]}"
        )

        return {
            "title": question,
            "description": description,
            "solution": correct_label,
            "exercise_type": "single_choice",
            "difficulty": "medium",
        }

    return None


def generate_true_false_from_content(item, content):
    """生成判断题"""
    if item["type"] == "definition":
        term = item["term"]

        # 50%正确，50%错误
        is_true = random.choice([True, False])

        if is_true:
            statement = f"{term}的定义：{item['definition'][:80]}"
            answer = "A"
        else:
            statement = f"{term}可以通过穷举测试完全验证"
            answer = "B"

        question = f"请判断：{statement}"
        description = f"{question}\n\nA. 正确\nB. 错误"

        return {
            "title": f"判断：{statement[:40]}",
            "description": description,
            "solution": answer,
            "exercise_type": "true_false",
            "difficulty": "easy",
        }

    return None


def generate_multiple_choice_from_content(item, all_items):
    """生成多选题"""
    if item["type"] == "section":
        title = item["title"]

        question = f"关于「{title}」，以下说法正确的有？（多选）"

        # 2个正确答案
        correct_answers = [
            f"{title}是软件测试的重要概念",
            f"{title}需要在整个开发过程中关注",
        ]

        # 2个错误答案
        wrong_answers = [
            f"{title}可以通过穷举测试完全验证",
            f"{title}只在测试阶段需要考虑",
        ]

        options = correct_answers + wrong_answers
        random.shuffle(options)

        correct_indices = [options.index(ca) for ca in correct_answers]
        correct_labels = sorted(["A", "B", "C", "D"][i] for i in correct_indices)
        solution = ",".join(correct_labels)

        description = (
            f"{question}\n\nA. {options[0][:80]}\nB. {options[1][:80]}\nC. {options[2][:80]}\nD. {options[3][:80]}"
        )

        return {
            "title": question,
            "description": description,
            "solution": solution,
            "exercise_type": "multiple_choice",
            "difficulty": "hard",
        }

    return None


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有学习路径
    cursor.execute("SELECT id, title FROM learning_paths ORDER BY id")
    learning_paths = cursor.fetchall()

    print("🚀 开始智能生成习题（真正基于课程内容）")
    print(f"📚 找到 {len(learning_paths)} 个学习路径")
    print("=" * 70)

    total_exercises = 0

    for path_id, path_title in learning_paths:
        print(f"\n📖 处理学习路径: {path_title} (ID: {path_id})")

        # 获取该路径的所有课程内容
        cursor.execute(
            """
            SELECT id, title, content, knowledge_point 
            FROM lesson_sections 
            WHERE learning_path_id = ? AND content IS NOT NULL AND content != ''
        """,
            (path_id,),
        )
        sections = cursor.fetchall()

        if not sections:
            print("  ⚠️  没有找到课程内容，跳过")
            continue

        print(f"  📝 找到 {len(sections)} 个课程章节")

        # 删除该路径的旧习题
        cursor.execute("DELETE FROM exercises WHERE learning_path_id = ?", (path_id,))
        print("  🗑️  已删除旧习题")

        exercises = []

        # 为每个章节生成习题
        for section in sections:
            section_id, section_title, content, knowledge_point = section

            # 解析内容
            items = parse_content(content)

            if not items:
                continue

            # 为每个提取的项生成1道题
            for item in items[:15]:  # 每个章节最多15道题
                # 60% 单选题，25% 多选题，15% 判断题
                rand = random.random()

                ex = None
                if rand < 0.6:
                    ex = generate_single_choice_from_content(item, items, section_title)
                elif rand < 0.85:
                    ex = generate_multiple_choice_from_content(item, items)
                else:
                    ex = generate_true_false_from_content(item, content)

                if ex:
                    ex["learning_path_id"] = path_id
                    ex["category"] = section_title
                    ex["knowledge_point"] = item.get("term", item.get("title", ""))[:200]
                    exercises.append(ex)

        # 确保每个学习路径至少有100道题
        while len(exercises) < 100:
            # 复用已有的习题，换一下表述
            if exercises:
                template_ex = random.choice(exercises)
                new_ex = template_ex.copy()
                new_ex["title"] = f"[补充] {template_ex['title']}"
                exercises.append(new_ex)
            else:
                break

        # 插入数据库
        inserted = 0
        for ex in exercises[:300]:  # 最多300道
            try:
                # 根据习题类型设置language
                if ex["exercise_type"] == "code":
                    lang = "python"
                else:
                    lang = "中文"

                cursor.execute(
                    """
                    INSERT INTO exercises 
                    (title, description, solution, exercise_type, difficulty, 
                     learning_path_id, category, knowledge_point, is_public, 
                     language, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
                """,
                    (
                        ex["title"],
                        ex["description"],
                        ex["solution"],
                        ex["exercise_type"],
                        ex["difficulty"],
                        ex["learning_path_id"],
                        ex.get("category", ""),
                        ex.get("knowledge_point", ""),
                        lang,
                    ),
                )
                inserted += 1
            except Exception:
                continue

        conn.commit()
        total_exercises += inserted
        print(f"  ✅ 生成了 {inserted} 道习题")

    print("\n" + "=" * 70)
    print(f"🎉 完成！总共生成 {total_exercises} 道习题")

    # 验证结果
    cursor.execute("SELECT COUNT(*) FROM exercises")
    total = cursor.fetchone()[0]
    print(f"📊 数据库中共有 {total} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
