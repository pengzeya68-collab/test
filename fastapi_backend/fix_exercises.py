#!/usr/bin/env python3
"""
修复现有习题 - 根据课程内容更新现有习题
不删除，只更新 title/description/answer
"""

import sqlite3
import re
import random

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"


def extract_key_concepts(content):
    """从课程内容中提取关键概念"""
    concepts = []

    # 提取 **粗体** 术语
    bold_terms = re.findall(r"\*\*(.+?)\*\*", content)
    concepts.extend(bold_terms)

    # 提取 ## 标题
    headings = re.findall(r"##\s+(.+)", content)
    concepts.extend(headings)

    # 提取 ### 小标题
    subheadings = re.findall(r"###\s+(.+)", content)
    concepts.extend(subheadings)

    return list(set(concepts))[:20]  # 去重，最多20个


def fix_exercise(exercise, content, key_concepts):
    """根据课程内容修复一道习题"""
    ex_id, title, desc, solution, ex_type, path_id = exercise

    # 如果课程内容为空，跳过
    if not content:
        return None

    # 随机选择一个关键概念来生成题目
    if key_concepts:
        concept = random.choice(key_concepts)
    else:
        # 从内容中提取第一句话作为概念
        sentences = re.split(r"[。！？]", content)
        concept = sentences[0][:30] if sentences else "软件测试"

    # 根据习题类型生成正确的题目
    if ex_type == "single_choice":
        return generate_single_choice(ex_id, concept, content)
    elif ex_type == "multiple_choice":
        return generate_multiple_choice(ex_id, concept, content)
    elif ex_type == "true_false":
        return generate_true_false(ex_id, concept, content)
    elif ex_type == "code":
        return generate_code_question(ex_id, concept, content)
    else:
        return None


def generate_single_choice(ex_id, concept, content):
    """生成单选题"""
    # 从内容中找相关句子作为正确答案
    sentences = re.split(r"[。！？]", content)
    relevant_sentences = [s for s in sentences if concept in s]

    if relevant_sentences:
        correct_answer = relevant_sentences[0][:80]
    else:
        correct_answer = f"{concept}是软件测试中的重要概念"

    # 生成错误选项
    wrong_answers = [
        f"{concept}与软件测试无关",
        f"{concept}只在开发阶段使用",
        f"{concept}可以通过穷举测试验证",
    ]

    options = [correct_answer] + wrong_answers
    random.shuffle(options)

    correct_label = ["A", "B", "C", "D"][options.index(correct_answer)]

    question = f"关于「{concept}」，以下说法正确的是？"
    description = f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}"

    return {
        "id": ex_id,
        "title": question,
        "description": description,
        "solution": correct_label,
    }


def generate_multiple_choice(ex_id, concept, content):
    """生成多选题"""
    question = f"关于「{concept}」，以下说法正确的有？（多选）"

    # 2个正确答案
    correct_answers = [
        f"{concept}是软件测试的重要概念",
        f"{concept}需要在整个开发过程中关注",
    ]

    # 2个错误答案
    wrong_answers = [
        f"{concept}可以通过穷举测试完全验证",
        f"{concept}只在测试阶段需要考虑",
    ]

    options = correct_answers + wrong_answers
    random.shuffle(options)

    correct_indices = [options.index(ca) for ca in correct_answers]
    correct_labels = sorted(["A", "B", "C", "D"][i] for i in correct_indices)
    solution = ",".join(correct_labels)

    description = f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}"

    return {
        "id": ex_id,
        "title": question,
        "description": description,
        "solution": solution,
    }


def generate_true_false(ex_id, concept, content):
    """生成判断题"""
    # 50% 正确，50% 错误
    is_true = random.choice([True, False])

    if is_true:
        # 从内容中找相关句子
        sentences = re.split(r"[。！？]", content)
        relevant = [s for s in sentences if concept in s]
        if relevant:
            statement = relevant[0][:80]
        else:
            statement = f"{concept}是软件测试中的重要概念"
        answer = "A"
    else:
        statement = f"{concept}可以通过穷举测试完全验证"
        answer = "B"

    question = f"请判断：{statement}"
    description = f"{question}\n\nA. 正确\nB. 错误"

    return {
        "id": ex_id,
        "title": f"判断：{statement[:40]}",
        "description": description,
        "solution": answer,
    }


def generate_code_question(ex_id, concept, content):
    """生成代码题"""
    question = f"请编写一个函数来测试{concept}"

    description = f"""{question}

要求：
1. 函数接收必要的参数
2. 返回测试结果
3. 包含必要的错误处理

示例：
输入：有效的输入
输出：测试通过
"""

    return {
        "id": ex_id,
        "title": question,
        "description": description,
        "solution": "A",  # 代码题答案通常是A（通过）
    }


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 开始修复现有习题")
    print("=" * 70)

    # 获取所有学习路径
    cursor.execute("SELECT id, title FROM learning_paths ORDER BY id")
    learning_paths = cursor.fetchall()

    total_fixed = 0

    for path_id, path_title in learning_paths:
        print(f"\n📖 修复学习路径: {path_title} (ID: {path_id})")

        # 获取该路径的课程内容
        cursor.execute(
            """
            SELECT content FROM lesson_sections 
            WHERE learning_path_id = ? AND content IS NOT NULL AND content != ''
        """,
            (path_id,),
        )
        sections = cursor.fetchall()

        if not sections:
            print("  ⚠️  没有课程内容，跳过")
            continue

        # 合并所有课程内容
        all_content = "\n\n".join([s[0] for s in sections])

        # 提取关键概念
        key_concepts = extract_key_concepts(all_content)
        print(f"  📝 提取了 {len(key_concepts)} 个关键概念")

        # 获取该路径的所有习题
        cursor.execute(
            """
            SELECT id, title, description, solution, exercise_type, learning_path_id
            FROM exercises 
            WHERE learning_path_id = ?
        """,
            (path_id,),
        )
        exercises = cursor.fetchall()

        print(f"  📊 找到 {len(exercises)} 道习题")

        # 修复每道习题
        fixed_count = 0
        for exercise in exercises:
            fixed = fix_exercise(exercise, all_content, key_concepts)

            if fixed:
                try:
                    cursor.execute(
                        """
                        UPDATE exercises 
                        SET title = ?, description = ?, solution = ?
                        WHERE id = ?
                    """,
                        (
                            fixed["title"],
                            fixed["description"],
                            fixed["solution"],
                            fixed["id"],
                        ),
                    )
                    fixed_count += 1
                except Exception as e:
                    print(f"  ⚠️  修复失败 (ID {fixed['id']}): {e}")

        conn.commit()
        total_fixed += fixed_count
        print(f"  ✅ 修复了 {fixed_count} 道习题")

    print("\n" + "=" * 70)
    print(f"🎉 完成！总共修复 {total_fixed} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
