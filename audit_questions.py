"""
面试题目质量审计脚本
检测实用性、重复、难度分级、与项目适配性
"""
import re
from sqlalchemy import create_engine, select, func, or_, and_
from sqlalchemy.orm import sessionmaker
from fastapi_backend.models.models import InterviewQuestion

DATABASE_URL = "sqlite:///./instance/testmaster.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 60)
print("面试题目质量审计报告")
print("=" * 60)

# 1. 基础统计
total = session.execute(select(func.count(InterviewQuestion.id))).scalar()
print(f"\n总题目数: {total}")

# 2. 各分类数量
counts = session.execute(
    select(InterviewQuestion.category, func.count(InterviewQuestion.id))
    .group_by(InterviewQuestion.category)
    .order_by(func.count(InterviewQuestion.id).desc())
).all()

print(f"\n【各分类分布】")
cat_counts = {}
for cat, cnt in counts:
    cat_counts[cat] = cnt
    print(f"  {cat}: {cnt}")

# 3. 难度分布
diff_counts = session.execute(
    select(InterviewQuestion.difficulty, func.count(InterviewQuestion.id))
    .group_by(InterviewQuestion.difficulty)
).all()
print(f"\n【难度分布】")
for diff, cnt in diff_counts:
    print(f"  {diff}: {cnt}")

# 4. 数据质量检查
empty_title = session.execute(select(func.count(InterviewQuestion.id)).where(
    or_(InterviewQuestion.title == '', InterviewQuestion.title == None)
)).scalar()
empty_answer = session.execute(select(func.count(InterviewQuestion.id)).where(
    or_(InterviewQuestion.answer == '', InterviewQuestion.answer == None)
)).scalar()

print(f"\n【数据质量】")
print(f"  空标题: {empty_title}")
print(f"  空答案: {empty_answer}")

# 5. 答案长度分析
all_questions = session.execute(select(InterviewQuestion)).scalars().all()
valid_answers = [q.answer for q in all_questions if q.answer and len(q.answer.strip()) > 0]

print(f"\n【答案长度分析】")
print(f"  有答案的题目: {len(valid_answers)}")

if valid_answers:
    lens = [len(a) for a in valid_answers]
    short = [a for a in valid_answers if len(a) < 50]
    good = [a for a in valid_answers if len(a) >= 100]
    print(f"  最短: {min(lens)}字符")
    print(f"  最长: {max(lens)}字符")
    print(f"  平均: {sum(lens)//len(lens)}字符")
    print(f"  过短(<50字): {len(short)}道 (建议修复)")
    print(f"  较好(>=100字): {len(good)}道")

# 6. 相似标题检测
print(f"\n【相似/重复标题检测】")

def extract_keywords(title):
    """提取标题关键词"""
    if not title:
        return set()
    chinese = re.findall(r'[\u4e00-\u9fa5]{2,}', title)
    english = re.findall(r'[a-zA-Z0-9]{3,}', title)
    keywords = set(chinese + english)
    stopwords = {'如何', '怎么', '什么', '为什么', '是否', '应该', '可以', '一个', '对于', '关于', '讲解', '说说'}
    return keywords - stopwords

similar_groups = []
checked = set()

for i, q1 in enumerate(all_questions):
    if q1.id in checked or not q1.title:
        continue
    group = [q1]
    keywords1 = extract_keywords(q1.title)

    for q2 in all_questions[i+1:]:
        if q2.id in checked or not q2.title:
            continue
        keywords2 = extract_keywords(q2.title)
        if keywords1 and keywords2:
            intersection = keywords1 & keywords2
            if len(intersection) >= 3:
                group.append(q2)
                checked.add(q2.id)

    if len(group) > 1:
        similar_groups.append(group)
        for q in group:
            checked.add(q.id)

print(f"  发现 {len(similar_groups)} 组相似题目（共 {sum(len(g) for g in similar_groups)} 道）")
for idx, group in enumerate(similar_groups[:5]):
    print(f"\n  相似组{idx+1} ({len(group)}道):")
    for q in group[:3]:
        print(f"    - {q.title[:50]}")

# 7. 实用性评估
print(f"\n【实用性评估】")

scenario_keywords = ['遇到', '发现', '碰到', '处理', '解决', '实战', '实际', '项目', '经验', '场景']
theory_keywords = ['定义', '概念', '什么是', '解释', '简述', '描述', '的区别', '是什么']

practice_questions = []
theory_questions = []

for q in all_questions:
    if not q.title:
        continue
    title = q.title
    is_scenario = any(kw in title for kw in scenario_keywords)
    is_theory = any(kw in title for kw in theory_keywords)

    if is_scenario:
        practice_questions.append(q)
    elif is_theory:
        theory_questions.append(q)

print(f"  场景实践题: {len(practice_questions)}道 (考察实际工作能力) ★★★")
print(f"  理论概念题: {len(theory_questions)}道 (考察基础知识) ★★")
print(f"  中性题目: {total - len(practice_questions) - len(theory_questions)}道")

# 8. 适配性评估
print(f"\n【与项目适配性评估】")

project_categories = {
    '测试理论': '基础必备',
    '测试用例设计': '核心技能',
    '缺陷管理': '核心技能',
    'Python编程': '工具开发',
    'Web测试': '功能测试',
    'API测试': '接口测试',
    '自动化测试': '自动化',
    '性能测试': '专项测试',
    '安全测试': '专项测试',
    'Linux': '运维基础',
    '数据库': '运维基础',
    '计算机基础': '基础必备',
}

for cat, desc in project_categories.items():
    count = cat_counts.get(cat, 0)
    status = "✓" if count >= 20 else "△" if count > 0 else "○"
    print(f"  {status} {cat}: {count}道 - {desc}")

# 9. 答案过短的具体问题
print(f"\n【需要修复的题目（答案过短）】")
short_questions = session.execute(
    select(InterviewQuestion).where(
        and_(
            InterviewQuestion.answer != None,
            func.length(InterviewQuestion.answer) < 50
        )
    )
).scalars().all()

print(f"  共 {len(short_questions)} 道答案过短")
for q in short_questions[:3]:
    ans = q.answer[:30] if q.answer else "空"
    print(f"  [{q.category}] {q.title[:40]}...")
    print(f"    答案: {ans}...")

print("\n" + "=" * 60)
print("审计完成")
print("=" * 60)

session.close()
