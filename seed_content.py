"""
TestMaster 内容填充脚本 - 大幅扩展版
填充完整的测试技术学习内容体系
包括：学习路径、练习题、面试题、考试题、成就
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from fastapi_backend.core.database import AsyncSessionLocal, engine, Base
from fastapi_backend.models.models import (
    LearningPath, Exercise, InterviewQuestion, Exam, ExamQuestion, Achievement
)

ADMIN_ID = 1

# ============================================================
# 学习路径 (11条)
# ============================================================
LEARNING_PATHS = [
    {"title": "软件测试基础入门", "description": "从零开始学习软件测试的核心概念、流程和方法，建立测试思维的基础框架。适合零基础转行或刚入行的测试人员。", "learning_objectives": "掌握软件测试的基本概念和分类\n理解软件开发生命周期中的测试角色\n学会编写基础测试用例\n了解缺陷管理流程\n掌握测试文档规范", "knowledge_outline": "1. 软件测试概述与发展历史\n2. 软件测试的基本原则\n3. 测试的分类：黑盒/白盒/灰盒\n4. 测试用例设计方法概述\n5. 缺陷生命周期管理\n6. 测试文档规范\n7. 测试环境管理基础", "supporting_resources": "《软件测试的艺术》\nISTQB基础级大纲\nGoogle Testing Blog", "prerequisites": "无前置要求，适合零基础入门", "language": "通用", "difficulty": "beginner", "stage": 1, "estimated_hours": 20},
    {"title": "功能测试实战", "description": "深入学习功能测试的实战技能，掌握等价类划分、边界值分析、因果图等核心用例设计方法。", "learning_objectives": "熟练运用等价类划分法\n掌握边界值分析方法\n学会使用因果图和判定表\n掌握场景法和状态迁移测试\n能独立完成功能测试方案设计", "knowledge_outline": "1. 等价类划分法详解与实战\n2. 边界值分析方法\n3. 因果图与判定表\n4. 场景法与状态迁移测试\n5. 正交实验法\n6. 错误推测法\n7. 功能测试方案编写规范", "supporting_resources": "《软件测试方法与技术》\n测试用例设计实战案例集", "prerequisites": "软件测试基础入门", "language": "通用", "difficulty": "beginner", "stage": 1, "estimated_hours": 25},
    {"title": "接口测试与自动化", "description": "系统学习API接口测试的理论与实践，掌握Postman、Requests等工具，实现接口自动化测试。", "learning_objectives": "理解HTTP协议与RESTful API\n熟练使用Postman进行接口测试\n掌握Python Requests库\n能编写接口自动化测试框架\n掌握数据驱动与参数化测试", "knowledge_outline": "1. HTTP协议与API基础\n2. RESTful API设计规范\n3. Postman使用进阶\n4. Python Requests库实战\n5. 接口自动化框架设计\n6. 数据驱动与参数化测试\n7. 接口安全测试\n8. Mock服务与契约测试", "supporting_resources": "Postman官方文档\nPython Requests文档\n《接口测试实战》", "prerequisites": "Python基础、软件测试基础", "language": "Python", "difficulty": "intermediate", "stage": 2, "estimated_hours": 30},
    {"title": "Web UI自动化测试", "description": "掌握Selenium WebDriver的核心技术，实现Web应用的UI自动化测试，包括POM设计模式和CI集成。", "learning_objectives": "熟练使用Selenium WebDriver\n掌握元素定位与操作方法\n理解POM设计模式\n掌握数据驱动测试\n能集成到CI/CD流水线", "knowledge_outline": "1. Selenium WebDriver基础\n2. 八大元素定位策略\n3. 显式等待与隐式等待\n4. POM设计模式实战\n5. 数据驱动测试\n6. Allure测试报告\n7. 多窗口与iframe处理\n8. CI/CD集成", "supporting_resources": "Selenium官方文档\n《Selenium实战》\nAllure Framework文档", "prerequisites": "Python基础、HTML/CSS基础", "language": "Python", "difficulty": "intermediate", "stage": 2, "estimated_hours": 35},
    {"title": "性能测试工程", "description": "深入学习性能测试理论与工具，掌握JMeter/Locust进行负载测试、压力测试和稳定性测试。", "learning_objectives": "理解性能测试核心指标\n熟练使用JMeter进行性能测试\n掌握Locust编写性能脚本\n能分析性能瓶颈并优化\n掌握性能测试报告编写", "knowledge_outline": "1. 性能测试理论体系\n2. 关键性能指标（TPS/QPS/RT）\n3. JMeter脚本开发\n4. JMeter分布式压测\n5. Locust性能框架\n6. 性能瓶颈分析与调优\n7. 性能测试报告编写\n8. APM工具使用", "supporting_resources": "JMeter官方文档\nLocust官方文档\n《性能测试实战》", "prerequisites": "软件测试基础、Python基础", "language": "Python", "difficulty": "intermediate", "stage": 2, "estimated_hours": 30},
    {"title": "持续集成与DevOps测试", "description": "学习CI/CD流水线中的测试策略，掌握Jenkins、Docker、Git等工具在测试中的应用。", "learning_objectives": "理解CI/CD中的测试策略\n掌握Jenkins Pipeline配置\n学会Docker容器化测试\n能搭建自动化测试流水线\n掌握质量门禁配置", "knowledge_outline": "1. CI/CD基础概念\n2. Jenkins Pipeline配置\n3. Git工作流与代码审查\n4. Docker容器化测试环境\n5. 测试左移与质量门禁\n6. 自动化测试报告集成\n7. Kubernetes测试部署", "supporting_resources": "Jenkins官方文档\nDocker官方文档\n《持续交付》", "prerequisites": "自动化测试基础、Linux基础", "language": "通用", "difficulty": "advanced", "stage": 3, "estimated_hours": 25},
    {"title": "安全测试基础", "description": "学习Web安全测试的核心知识，掌握OWASP Top 10漏洞的测试方法和工具使用。", "learning_objectives": "理解Web安全测试体系\n掌握OWASP Top 10漏洞原理\n学会使用Burp Suite等工具\n能编写安全测试方案\n掌握安全漏洞修复建议", "knowledge_outline": "1. Web安全测试概述\n2. OWASP Top 10漏洞详解\n3. SQL注入测试\n4. XSS跨站脚本测试\n5. CSRF与认证漏洞\n6. Burp Suite使用实战\n7. 安全测试报告编写\n8. 自动化安全扫描", "supporting_resources": "OWASP官方文档\nBurp Suite文档\n《Web安全测试》", "prerequisites": "Web基础、HTTP协议", "language": "通用", "difficulty": "advanced", "stage": 3, "estimated_hours": 25},
    {"title": "移动端测试", "description": "掌握移动应用测试的核心技能，包括Appium自动化、兼容性测试和移动端性能测试。", "learning_objectives": "理解移动端测试特点\n掌握Appium自动化框架\n学会兼容性测试策略\n能进行移动端性能测试\n掌握移动端专项测试", "knowledge_outline": "1. 移动端测试概述\n2. Android/iOS测试环境搭建\n3. Appium自动化框架\n4. 移动端元素定位\n5. 兼容性测试策略\n6. 移动端性能与耗电测试\n7. 移动端弱网与中断测试", "supporting_resources": "Appium官方文档\nAndroid开发者文档\niOS测试指南", "prerequisites": "自动化测试基础", "language": "Python", "difficulty": "intermediate", "stage": 2, "estimated_hours": 25},
    {"title": "测试开发与工程化", "description": "从测试工程师进阶为测试开发，掌握测试平台开发、测试工具链建设和质量工程体系。", "learning_objectives": "掌握测试平台开发技能\n理解质量工程体系\n能设计测试工具链\n具备测试架构设计能力\n掌握质量度量与持续改进", "knowledge_outline": "1. 测试开发概述与能力模型\n2. 测试平台架构设计\n3. FastAPI/Django测试平台开发\n4. 测试数据管理\n5. 测试工具链建设\n6. 质量度量与持续改进\n7. 测试效能提升", "supporting_resources": "FastAPI文档\nDjango文档\n《Google软件测试之道》", "prerequisites": "Python进阶、Web开发基础", "language": "Python", "difficulty": "advanced", "stage": 3, "estimated_hours": 40},
    {"title": "数据库测试", "description": "学习数据库测试的核心方法，包括SQL基础、存储过程测试、数据迁移验证和数据库性能测试。", "learning_objectives": "掌握SQL查询与数据验证\n学会存储过程和触发器测试\n掌握数据迁移验证方法\n理解数据库性能测试\n能设计数据库测试方案", "knowledge_outline": "1. SQL基础与查询验证\n2. 存储过程与触发器测试\n3. 数据完整性约束测试\n4. 数据迁移与ETL测试\n5. 数据库性能测试\n6. 数据安全与权限测试\n7. 数据库自动化测试", "supporting_resources": "《SQL必知必会》\nMySQL官方文档\nPostgreSQL文档", "prerequisites": "软件测试基础、SQL基础", "language": "SQL", "difficulty": "intermediate", "stage": 2, "estimated_hours": 20},
    {"title": "测试管理与团队协作", "description": "学习测试项目管理、团队协作和质量保障体系建设的核心方法。", "learning_objectives": "掌握测试项目管理方法\n理解质量保障体系建设\n学会测试团队管理\n掌握测试流程优化\n能制定测试策略与计划", "knowledge_outline": "1. 测试项目管理基础\n2. 测试策略与计划制定\n3. 测试团队建设与管理\n4. 质量保障体系建设\n5. 测试流程优化与改进\n6. 风险管理与应急处理\n7. 跨团队协作与沟通", "supporting_resources": "《软件测试管理》\nISTQB高级大纲\n《质量免费》", "prerequisites": "3年以上测试经验", "language": "通用", "difficulty": "advanced", "stage": 3, "estimated_hours": 20},
]

# ============================================================
# 练习题 (50+道) - 由外部数据文件加载
# ============================================================
EXERCISES_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_exercises.json")
INTERVIEW_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_interviews.json")
EXAM_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_exams.json")

ACHIEVEMENTS = [
    {"key": "first_login", "name": "初来乍到", "description": "首次登录平台", "icon": "star", "category": "入门", "threshold": 1, "exp_reward": 10},
    {"key": "first_exercise", "name": "小试牛刀", "description": "完成第一道练习题", "icon": "pencil", "category": "练习", "threshold": 1, "exp_reward": 15},
    {"key": "exercise_10", "name": "勤学苦练", "description": "完成10道练习题", "icon": "book", "category": "练习", "threshold": 10, "exp_reward": 50},
    {"key": "exercise_30", "name": "题海战术", "description": "完成30道练习题", "icon": "books", "category": "练习", "threshold": 30, "exp_reward": 100},
    {"key": "exercise_50", "name": "学海无涯", "description": "完成50道练习题", "icon": "graduation_cap", "category": "练习", "threshold": 50, "exp_reward": 200},
    {"key": "first_interview", "name": "面试初体验", "description": "完成第一次模拟面试", "icon": "microphone", "category": "面试", "threshold": 1, "exp_reward": 20},
    {"key": "interview_5", "name": "面试达人", "description": "完成5次模拟面试", "icon": "trophy", "category": "面试", "threshold": 5, "exp_reward": 50},
    {"key": "interview_10", "name": "面霸养成", "description": "完成10次模拟面试", "icon": "medal", "category": "面试", "threshold": 10, "exp_reward": 100},
    {"key": "first_exam", "name": "考场新手", "description": "完成第一次考试", "icon": "document", "category": "考试", "threshold": 1, "exp_reward": 20},
    {"key": "exam_pass", "name": "逢考必过", "description": "考试得分超过及格线", "icon": "check", "category": "考试", "threshold": 1, "exp_reward": 30},
    {"key": "exam_perfect", "name": "满分学霸", "description": "考试获得满分", "icon": "star2", "category": "考试", "threshold": 1, "exp_reward": 100},
    {"key": "exam_5", "name": "考试达人", "description": "完成5次考试", "icon": "clipboard", "category": "考试", "threshold": 5, "exp_reward": 80},
    {"key": "checkin_7", "name": "一周坚持", "description": "连续签到7天", "icon": "calendar", "category": "签到", "threshold": 7, "exp_reward": 50},
    {"key": "checkin_30", "name": "月度之星", "description": "连续签到30天", "icon": "crown", "category": "签到", "threshold": 30, "exp_reward": 200},
    {"key": "community_post", "name": "社区新星", "description": "在社区发布第一篇帖子", "icon": "chat", "category": "社区", "threshold": 1, "exp_reward": 15},
    {"key": "community_10", "name": "社区达人", "description": "发布10篇帖子", "icon": "forum", "category": "社区", "threshold": 10, "exp_reward": 80},
    {"key": "path_complete_1", "name": "初窥门径", "description": "完成第一条学习路径", "icon": "path", "category": "学习路径", "threshold": 1, "exp_reward": 50},
    {"key": "path_complete_3", "name": "登堂入室", "description": "完成3条学习路径", "icon": "rocket", "category": "学习路径", "threshold": 3, "exp_reward": 150},
    {"key": "path_complete_all", "name": "学贯中西", "description": "完成所有学习路径", "icon": "gem", "category": "学习路径", "threshold": 11, "exp_reward": 500},
    {"key": "code_exercise_10", "name": "代码战士", "description": "完成10道编程练习题", "icon": "code", "category": "编程", "threshold": 10, "exp_reward": 100},
]


def _load_json(filepath):
    import json
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


async def seed():
    async with AsyncSessionLocal() as db:
        # 1. 学习路径
        path_objs = []
        for i, p in enumerate(LEARNING_PATHS):
            existing = await db.scalar(select(LearningPath).where(LearningPath.title == p["title"]))
            if existing:
                path_objs.append(existing)
                print(f"  [skip] LearningPath: {p['title']}")
                continue
            obj = LearningPath(
                title=p["title"], description=p["description"],
                learning_objectives=p["learning_objectives"], knowledge_outline=p["knowledge_outline"],
                supporting_resources=p["supporting_resources"], prerequisites=p["prerequisites"],
                language=p["language"], difficulty=p["difficulty"], stage=p["stage"],
                estimated_hours=p["estimated_hours"], is_public=True, admin_id=ADMIN_ID,
            )
            db.add(obj)
            path_objs.append(obj)
            print(f"  [new] LearningPath: {p['title']}")
        await db.flush()

        # 2. 练习题
        exercises = _load_json(EXERCISES_DATA_FILE)
        for e in exercises:
            existing = await db.scalar(select(Exercise).where(Exercise.title == e["title"]))
            if existing:
                print(f"  [skip] Exercise: {e['title']}")
                continue
            lp_idx = e.get("learning_path_idx")
            lp_id = path_objs[lp_idx].id if lp_idx is not None and lp_idx < len(path_objs) else None
            obj = Exercise(
                title=e["title"], description=e.get("description", ""),
                instructions=e.get("instructions", ""), solution=e.get("solution", ""),
                difficulty=e.get("difficulty", "easy"), language=e.get("language", "通用"),
                module=e.get("module", "normal"), category=e.get("category", ""),
                stage=e.get("stage", 1), knowledge_point=e.get("knowledge_point", ""),
                time_estimate=e.get("time_estimate", 15), is_public=True,
                exercise_type=e.get("exercise_type", "text"),
                test_cases=e.get("test_cases"), code_template=e.get("code_template"),
                expected_output=e.get("expected_output"), admin_id=ADMIN_ID,
                learning_path_id=lp_id,
            )
            db.add(obj)
            print(f"  [new] Exercise: {e['title']}")
        await db.flush()

        # 3. 面试题
        interviews = _load_json(INTERVIEW_DATA_FILE)
        for q in interviews:
            existing = await db.scalar(select(InterviewQuestion).where(InterviewQuestion.title == q["title"]))
            if existing:
                print(f"  [skip] Interview: {q['title']}")
                continue
            obj = InterviewQuestion(
                title=q["title"], content=q.get("content", ""),
                answer=q.get("answer", ""), category=q.get("category", ""),
                position_level=q.get("position_level", "初级"),
                difficulty=q.get("difficulty", "medium"),
                tags=q.get("tags", ""), is_published=True,
            )
            db.add(obj)
            print(f"  [new] Interview: {q['title']}")
        await db.flush()

        # 4. 考试
        import json
        exams = _load_json(EXAM_DATA_FILE)
        for exam_data in exams:
            existing = await db.scalar(select(Exam).where(Exam.title == exam_data["title"]))
            if existing:
                print(f"  [skip] Exam: {exam_data['title']}")
                continue
            questions_data = exam_data.get("questions", [])
            exam = Exam(
                title=exam_data["title"], description=exam_data.get("description", ""),
                exam_type=exam_data.get("exam_type", "模拟考试"),
                difficulty=exam_data.get("difficulty", "medium"),
                duration=exam_data["duration"], total_score=exam_data["total_score"],
                pass_score=exam_data["pass_score"],
                is_published=exam_data.get("is_published", True),
                user_id=ADMIN_ID,
            )
            db.add(exam)
            await db.flush()

            for idx, q in enumerate(questions_data):
                eq = ExamQuestion(
                    exam_id=exam.id, question_type=q["question_type"],
                    content=q["content"],
                    options=json.dumps(q.get("options", []), ensure_ascii=False) if q.get("options") else None,
                    correct_answer=q.get("correct_answer", ""),
                    score=q.get("score", 5), analysis=q.get("analysis", ""),
                    sort_order=idx,
                )
                db.add(eq)
            print(f"  [new] Exam: {exam_data['title']} ({len(questions_data)} questions)")
        await db.flush()

        # 5. 成就
        for a in ACHIEVEMENTS:
            existing = await db.scalar(select(Achievement).where(Achievement.key == a["key"]))
            if existing:
                print(f"  [skip] Achievement: {a['name']}")
                continue
            obj = Achievement(
                key=a["key"], name=a["name"], description=a.get("description", ""),
                icon=a.get("icon", ""), category=a.get("category", ""),
                threshold=a.get("threshold", 1), exp_reward=a.get("exp_reward", 10),
            )
            db.add(obj)
            print(f"  [new] Achievement: {a['name']}")

        await db.commit()
        print("\n[OK] Content seeding completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("TestMaster Content Seeding Script")
    print("=" * 60)
    asyncio.run(seed())
