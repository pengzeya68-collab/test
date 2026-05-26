#!/usr/bin/env python3
"""
高质量习题生成 - 真正从课程内容提取知识点
策略：
1. 提取所有定义、原则、对比、列表项
2. 每个知识点生成1-2道题
3. 正确答案来自课程内容，错误答案是常见误解
"""
import sqlite3
import re
import random

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'

def extract_knowledge_points(content):
    """从课程内容中提取所有知识点"""
    if not content:
        return []
    
    points = []
    
    # 1. 提取定义（**术语**：定义）
    defs = re.findall(r'\*\*(.+?)\*\*[:：](.+)', content)
    for term, definition in defs:
        points.append({
            'type': 'definition',
            'term': term.strip(),
            'content': definition.strip()[:200]
        })
    
    # 2. 提取表格内容
    tables = re.findall(r'\|(.+)\|', content)
    if tables:
        points.append({
            'type': 'table',
            'content': '\n'.join(tables[:10])
        })
    
    # 3. 提取编号列表（1. 2. 3. 或 - 列表）
    numbered = re.findall(r'(?:^\d+[\.、]\s*|^-)\s*(.+)$', content, re.MULTILINE)
    for item in numbered[:15]:
        if len(item.strip()) > 10:  # 只保留有意义的列表项
            points.append({
                'type': 'list_item',
                'content': item.strip()
            })
    
    # 4. 提取 ## 标题（作为知识点）
    headings = re.findall(r'##\s+(.+)', content)
    for h in headings:
        points.append({
            'type': 'heading',
            'content': h.strip()
        })
    
    # 5. 提取 ### 小标题
    subheadings = re.findall(r'###\s+(.+)', content)
    for sh in subheadings:
        points.append({
            'type': 'subheading',
            'content': sh.strip()
        })
    
    # 6. 提取代码块前的说明
    code_intros = re.findall(r'(.+?)\n```', content)
    for intro in code_intros:
        if len(intro.strip()) > 5:
            points.append({
                'type': 'code_intro',
                'content': intro.strip()
            })
    
    return points

def generate_question_from_point(point, point_index):
    """从一个知识点生成一道题"""
    ptype = point['type']
    content = point['content']
    
    # 单选题模板
    if ptype == 'definition':
        term = point['term']
        definition = point['content']
        
        question = f"以下对「{term}」的描述，正确的是？"
        
        # 正确答案：使用真实定义
        correct = definition[:100] if len(definition) > 100 else definition
        
        # 错误答案：常见误解
        wrongs = [
            f"与{term}无关的概念",
            f"{term}只在测试阶段使用",
            f"{term}可以通过穷举测试完全验证"
        ]
        
        options = [correct] + wrongs
        random.shuffle(options)
        correct_label = ['A', 'B', 'C', 'D'][options.index(correct)]
        
        return {
            'title': question,
            'description': f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}",
            'solution': correct_label,
            'type': 'single_choice'
        }
    
    elif ptype == 'list_item':
        # 从列表项生成题
        item = content
        
        # 提取关键词（前20字符）
        keyword = item[:20] if len(item) > 20 else item
        
        question = f"关于「{keyword}」，以下说法正确的是？"
        
        correct = item
        wrongs = [
            f"{keyword}与软件测试无关",
            f"{keyword}只在开发阶段使用",
            f"{keyword}可以通过穷举测试验证"
        ]
        
        options = [correct] + wrongs
        random.shuffle(options)
        correct_label = ['A', 'B', 'C', 'D'][options.index(correct)]
        
        return {
            'title': question,
            'description': f"{question}\n\nA. {options[0][:80]}\nB. {options[1][:80]}\nC. {options[2][:80]}\nD. {options[3][:80]}",
            'solution': correct_label,
            'type': 'single_choice'
        }
    
    elif ptype == 'heading':
        heading = content
        
        question = f"关于「{heading}」，以下说法正确的是？"
        
        correct = f"{heading}是软件测试中的重要概念"
        wrongs = [
            f"{heading}与软件测试无关",
            f"{heading}只在开发阶段使用",
            f"{heading}可以通过穷举测试验证"
        ]
        
        options = [correct] + wrongs
        random.shuffle(options)
        correct_label = ['A', 'B', 'C', 'D'][options.index(correct)]
        
        return {
            'title': question,
            'description': f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}",
            'solution': correct_label,
            'type': 'single_choice'
        }
    
    elif ptype == 'subheading':
        sub = content
        
        # 50% 单选题，50% 多选题
        if random.random() < 0.5:
            question = f"关于「{sub}」，以下说法正确的是？"
            correct = f"{sub}是软件测试的重要概念"
            wrongs = [
                f"{sub}与软件测试无关",
                f"{sub}只在测试阶段需要考虑",
                f"{sub}可以通过穷举测试完全验证"
            ]
            
            options = [correct] + wrongs
            random.shuffle(options)
            correct_label = ['A', 'B', 'C', 'D'][options.index(correct)]
            
            return {
                'title': question,
                'description': f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}",
                'solution': correct_label,
                'type': 'single_choice'
            }
        else:
            question = f"关于「{sub}」，以下说法正确的有？（多选）"
            
            correct_answers = [
                f"{sub}是软件测试的重要概念",
                f"{sub}需要在整个开发过程中关注"
            ]
            
            wrongs = [
                f"{sub}可以通过穷举测试完全验证",
                f"{sub}只在测试阶段需要考虑"
            ]
            
            options = correct_answers + wrongs
            random.shuffle(options)
            
            correct_indices = [options.index(ca) for ca in correct_answers]
            correct_labels = sorted(['A', 'B', 'C', 'D'][i] for i in correct_indices)
            solution = ','.join(correct_labels)
            
            return {
                'title': question,
                'description': f"{question}\n\nA. {options[0]}\nB. {options[1]}\nC. {options[2]}\nD. {options[3]}",
                'solution': solution,
                'type': 'multiple_choice'
            }
    
    return None

def generate_true_false(point):
    """生成判断题"""
    content = point['content']
    
    # 随机选择正确或错误
    is_true = random.choice([True, False])
    
    if is_true:
        statement = content[:80] if len(content) > 80 else content
        answer = 'A'
    else:
        # 生成一个错误的陈述
        if 'definition' in point:
            statement = f"{point['term']}可以通过穷举测试完全验证"
        else:
            statement = f"{content[:50]}可以通过穷举测试完全验证"
        answer = 'B'
    
    question = f"请判断：{statement}"
    
    return {
        'title': f"判断：{statement[:40]}",
        'description': f"{question}\n\nA. 正确\nB. 错误",
        'solution': answer,
        'type': 'true_false'
    }

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title FROM learning_paths ORDER BY id")
    learning_paths = cursor.fetchall()
    
    print(f"🚀 开始生成高质量习题（真正基于课程内容）")
    print(f"📚 找到 {len(learning_paths)} 个学习路径")
    print("="*70)
    
    total_exercises = 0
    
    for path_id, path_title in learning_paths:
        print(f"\n📖 处理: {path_title} (ID: {path_id})")
        
        # 获取课程内容
        cursor.execute("""
            SELECT id, title, content 
            FROM lesson_sections 
            WHERE learning_path_id = ? AND content IS NOT NULL AND content != ''
        """, (path_id,))
        sections = cursor.fetchall()
        
        if not sections:
            print(f"  ⚠️  无课程内容，跳过")
            continue
        
        # 删除旧习题
        cursor.execute("DELETE FROM exercises WHERE learning_path_id = ?", (path_id,))
        print(f"  🗑️  已删除旧习题")
        
        # 提取所有知识点
        all_points = []
        for section_id, section_title, content in sections:
            points = extract_knowledge_points(content)
            all_points.extend(points)
        
        print(f"  📝 提取了 {len(all_points)} 个知识点")
        
        # 生成习题
        exercises = []
        used_points = set()
        
        for i, point in enumerate(all_points):
            # 避免重复
            point_key = f"{point['type']}:{point['content'][:50]}"
            if point_key in used_points:
                continue
            used_points.add(point_key)
            
            # 生成题目
            ex = generate_question_from_point(point, i)
            if ex:
                ex['learning_path_id'] = path_id
                ex['category'] = sections[0][1] if sections else ''
                exercises.append(ex)
            
            # 每个知识点还有30%概率生成判断题
            if random.random() < 0.3:
                tf_ex = generate_true_false(point)
                if tf_ex:
                    tf_ex['learning_path_id'] = path_id
                    tf_ex['category'] = sections[0][1] if sections else ''
                    exercises.append(tf_ex)
        
        # 如果不够50道，补充
        while len(exercises) < 50:
            if all_points:
                point = random.choice(all_points)
                ex = generate_question_from_point(point, 0)
                if ex:
                    ex['learning_path_id'] = path_id
                    ex['category'] = sections[0][1] if sections else ''
                    exercises.append(ex)
            else:
                break
        
        # 插入数据库
        inserted = 0
        for ex in exercises[:300]:  # 最多300道
            try:
                lang = "python" if ex['type'] == 'code' else "中文"
                
                cursor.execute("""
                    INSERT INTO exercises 
                    (title, description, solution, exercise_type, difficulty, 
                     learning_path_id, category, is_public, language, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
                """, (
                    ex['title'],
                    ex['description'],
                    ex['solution'],
                    ex['type'],
                    'medium',
                    ex['learning_path_id'],
                    ex.get('category', ''),
                    lang
                ))
                inserted += 1
            except Exception as e:
                continue
        
        conn.commit()
        total_exercises += inserted
        print(f"  ✅ 生成了 {inserted} 道习题")
    
    print("\n" + "="*70)
    print(f"🎉 完成！总共生成 {total_exercises} 道习题")
    
    cursor.execute("SELECT COUNT(*) FROM exercises")
    total = cursor.fetchone()[0]
    print(f"📊 数据库中共有 {total} 道习题")
    
    conn.close()

if __name__ == "__main__":
    main()
