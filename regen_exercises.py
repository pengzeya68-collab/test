"""
为已存在的学习路径重新生成练习数据
"""
import sqlite3
from datetime import datetime

main_db = 'instance/testmaster.db'
conn = sqlite3.connect(main_db)
c = conn.cursor()

# 获取所有 learning_paths
c.execute('SELECT id, title, language, difficulty, stage FROM learning_paths ORDER BY id')
paths = c.fetchall()
print(f'找到 {len(paths)} 个学习路径')

# 为每个路径生成练习
import random

def gen_exercises(path_id, path_title, stage):
    """根据路径标题生成合适的练习"""
    exercises = []

    topic_map = {
        '软件测试': [
            ('测试用例的分类与定义', '理解测试用例的各种分类方法', 'choice', 'beginner'),
            ('缺陷原理 - 生命周期', '掌握软件缺陷从发现到关闭的完整生命周期', 'choice', 'beginner'),
            ('黑盒与白盒测试的核心区别', '理解两种测试方法在测试重点和实现方式上的差异', 'choice', 'intermediate'),
            ('测试计划包含哪些核心内容', '掌握测试计划文档的关键要素', 'choice', 'intermediate'),
            ('V模型各阶段的测试类型', '理解V模型中单元测试、集成测试、系统测试的关系', 'choice', 'beginner'),
        ],
        'SQL': [
            ('SELECT查询基础', '掌握SELECT语句的基本用法', 'sql', 'beginner'),
            ('GROUP BY聚合函数', '理解COUNT/SUM/AVG等聚合函数的使用', 'sql', 'intermediate'),
            ('多表JOIN查询', '掌握INNER/LEFT/RIGHT JOIN的区别', 'sql', 'intermediate'),
            ('子查询实战', '理解嵌套SELECT的用法', 'sql', 'advanced'),
        ],
        '计算机基础': [
            ('HTTP状态码识别', '掌握2xx/4xx/5xx状态码的含义', 'choice', 'beginner'),
            ('GET与POST方法区别', '理解两种HTTP方法的适用场景', 'choice', 'beginner'),
            ('TCP三次握手流程', '理解TCP连接建立的完整过程', 'choice', 'intermediate'),
        ],
        'Linux': [
            ('文件权限chmod命令', '掌握Linux文件权限的数字表示法', 'choice', 'beginner'),
            ('grep搜索日志内容', '使用grep命令在日志中查找关键信息', 'code', 'beginner'),
            ('tail实时查看日志', '使用tail -f 实时监控日志变化', 'code', 'beginner'),
        ],
        '测试计划': [
            ('测试计划的主要内容', '理解测试计划文档的核心组成', 'choice', 'intermediate'),
            ('测试策略选择', '了解不同测试策略的适用场景', 'choice', 'intermediate'),
        ],
        '接口测试': [
            ('RESTful API规范', '理解RESTful接口设计基本原则', 'choice', 'intermediate'),
            ('接口测试用例设计', '掌握接口测试用例的编写方法', 'choice', 'intermediate'),
            ('Postman工具使用', '使用Postman发送HTTP请求测试接口', 'code', 'beginner'),
            ('接口鉴权Token处理', '理解Bearer Token鉴权机制', 'code', 'intermediate'),
        ],
        'Python': [
            ('Python列表操作', '掌握Python列表的增删改查', 'code', 'beginner'),
            ('Python字典操作', '熟练使用字典存储键值对数据', 'code', 'beginner'),
            ('Python字符串处理', '掌握字符串切片和常用方法', 'code', 'intermediate'),
            ('Python文件读取操作', '使用Python读取和处理文件', 'code', 'intermediate'),
            ('Python异常处理', '理解try-except的用法', 'code', 'beginner'),
        ],
        'Selenium': [
            ('Selenium元素定位', '掌握ID/Name/XPath/CSS定位方法', 'choice', 'intermediate'),
            ('隐式等待与显式等待', '理解Selenium等待机制的优缺点', 'choice', 'intermediate'),
            ('编写Selenium登录测试', '使用Selenium完成登录自动化测试', 'code', 'advanced'),
            ('POM页面对象模式', '理解POM设计模式的核心思想', 'choice', 'advanced'),
        ],
        'Requests': [
            ('Requests发送POST请求', '使用Python requests发送JSON请求', 'code', 'intermediate'),
            ('Pytest参数化测试', '使用@pytest.mark.parametrize实现数据驱动', 'code', 'advanced'),
            ('接口自动化测试全覆盖', '理解如何设计完整的接口自动化测试方案', 'choice', 'advanced'),
        ],
        '性能测试': [
            ('性能测试核心指标', '理解TPS、响应时间、并发数的含义', 'choice', 'intermediate'),
            ('Locust编写脚本', '使用Locust编写性能测试脚本', 'code', 'advanced'),
        ],
        '安全测试': [
            ('SQL注入识别', '理解SQL注入的原理和危害', 'choice', 'intermediate'),
            ('XSS攻击类型', '区分存储型、反射型、DOM型XSS', 'choice', 'intermediate'),
            ('CSRF攻击原理', '理解CSRF跨站请求伪造的机制', 'choice', 'intermediate'),
        ],
        'AI': [
            ('AI辅助测试应用场景', '了解AI在测试领域的典型应用', 'choice', 'advanced'),
            ('视觉回归测试原理', '理解基于图像对比的回归测试方法', 'choice', 'advanced'),
        ],
        'DevOps': [
            ('Docker容器基础命令', '掌握Docker镜像和容器的基本操作', 'choice', 'intermediate'),
            ('Jenkins Pipeline语法', '理解Jenkinsfile的编写方法', 'choice', 'advanced'),
            ('持续集成流水线设计', '理解CI/CD流水线的设计原则', 'choice', 'advanced'),
        ],
    }

    # 根据标题关键词匹配
    for key, exs in topic_map.items():
        if key in path_title:
            for title, desc, ex_type, diff in exs:
                exercises.append({
                    'title': title,
                    'description': desc,
                    'instructions': f'请完成以下{title}相关的练习',
                    'solution': '',
                    'difficulty': diff,
                    'language': '中文',
                    'module': 'normal',
                    'category': key,
                    'stage': stage,
                    'knowledge_point': key,
                    'time_estimate': 10,
                    'exercise_type': ex_type,
                })
            return exercises

    # 默认练习
    defaults = [
        ('理解本章节核心概念', '掌握本学习路径的主要知识点', 'choice', 'beginner'),
        ('完成综合练习题', '综合运用所学知识完成练习', 'choice', 'intermediate'),
    ]
    for title, desc, ex_type, diff in defaults:
        exercises.append({
            'title': title,
            'description': desc,
            'instructions': f'请完成以下{title}相关的练习',
            'solution': '',
            'difficulty': diff,
            'language': '中文',
            'module': 'normal',
            'category': path_title[:4],
            'stage': stage,
            'knowledge_point': path_title[:6],
            'time_estimate': 10,
            'exercise_type': ex_type,
        })
    return exercises

# 删除现有 linked exercises（以防有残留）
c.execute('DELETE FROM exercises WHERE learning_path_id IS NOT NULL AND learning_path_id IN (SELECT id FROM learning_paths)')
print(f'清除了残留 exercises')

# 为每个路径生成练习
total_created = 0
next_id = 1
c.execute('SELECT MAX(id) FROM exercises')
max_id = c.fetchone()[0] or 0
next_ex_id = max_id + 1

for path in paths:
    path_id, path_title, language, difficulty, stage = path
    exercises = gen_exercises(path_id, path_title, stage)
    print(f'路径 {path_id}: {path_title} → {len(exercises)} 条练习')

    for ex in exercises:
        c.execute('''
            INSERT INTO exercises (title, description, instructions, solution, difficulty,
                language, module, category, stage, knowledge_point, time_estimate,
                is_public, exercise_type, created_at, updated_at, user_id, admin_id, learning_path_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, NULL, NULL, ?)
        ''', (
            ex['title'], ex['description'], ex['instructions'], ex['solution'],
            ex['difficulty'], ex['language'], ex['module'], ex['category'],
            ex['stage'], ex['knowledge_point'], ex['time_estimate'],
            ex['exercise_type'],
            datetime.now().isoformat(), datetime.now().isoformat(),
            path_id
        ))
        next_ex_id += 1
        total_created += 1

conn.commit()

# 验证
print(f'\n=== 生成完成: 共 {total_created} 条练习 ===')
c.execute('''
    SELECT lp.id, lp.title, COUNT(e.id) as cnt
    FROM learning_paths lp
    LEFT JOIN exercises e ON e.learning_path_id = lp.id
    GROUP BY lp.id
    ORDER BY lp.id
''')
for r in c.fetchall():
    print(f'  LP id={r[0]}, exercises={r[2]}')

conn.close()
print('\nDone!')
