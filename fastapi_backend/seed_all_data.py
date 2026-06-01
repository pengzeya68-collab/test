"""
TestMaster 全量种子数据脚本
填充用户、社区、考试、面试题、签到、进度、自动化测试等所有数据
"""

import asyncio
import sys
import os
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import (
    Base,
    User,
    Exercise,
    Progress,
    Post,
    Comment,
    Like,
    Achievement,
    UserAchievement,
    DailyCheckin,
    Exam,
    ExamQuestion,
    InterviewQuestion,
    ApiGroup,
    ApiCase,
    Environment,
)
from fastapi_backend.services.auth_service import AuthService

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ================================================================
# 数据定义
# 注意: 以下为开发/测试用种子数据，生产环境部署后请立即修改默认密码！
# ================================================================

USERS = [
    {
        "username": "admin",
        "email": "admin@testmaster.com",
        "password": "admin123",  # 生产环境请在首次登录后立即修改！
        "is_admin": True,
        "is_super_admin": True,
        "avatar": None,
        "level": 50,
        "score": 9999,
        "study_time": 5000,
    },
    {
        "username": "zhangsan",
        "email": "zhangsan@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 25,
        "score": 3200,
        "study_time": 1800,
    },
    {
        "username": "lisi",
        "email": "lisi@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 18,
        "score": 2100,
        "study_time": 1200,
    },
    {
        "username": "wangwu",
        "email": "wangwu@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 30,
        "score": 4500,
        "study_time": 2400,
    },
    {
        "username": "zhaoliu",
        "email": "zhaoliu@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 12,
        "score": 1200,
        "study_time": 600,
    },
    {
        "username": "sunqi",
        "email": "sunqi@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 8,
        "score": 600,
        "study_time": 300,
    },
    {
        "username": "test_engineer",
        "email": "engineer@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 35,
        "score": 5800,
        "study_time": 3000,
    },
    {
        "username": "newbie",
        "email": "newbie@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 3,
        "score": 150,
        "study_time": 60,
    },
    {
        "username": "auto_test",
        "email": "autotest@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 40,
        "score": 7200,
        "study_time": 4200,
    },
    {
        "username": "dev_tester",
        "email": "dev@test.com",
        "password": "123456",
        "is_admin": False,
        "is_super_admin": False,
        "avatar": None,
        "level": 22,
        "score": 2800,
        "study_time": 1500,
    },
]

CATEGORIES = [
    "测试基础",
    "自动化测试",
    "性能测试",
    "安全测试",
    "面试经验",
    "工具分享",
    "职业发展",
    "学习心得",
]

POSTS = [
    {
        "title": "从零开始学测试，我的三个月成长之路",
        "category": "学习心得",
        "tags": "测试入门,学习经验",
        "is_essence": True,
        "is_top": True,
        "content": "三个月前我还是一个完全的测试小白，经过系统学习，现在成功拿到了心仪的Offer。在这里分享一下我的学习路线：\n\n### 第一阶段：基础理论\n- 《软件测试的艺术》一定要读\n- ISTQB基础级大纲可以帮你建立体系\n- 每天坚持做5道练习题\n\n### 第二阶段：实践练习\n- 在TestMaster上把所有基础路径刷完\n- 重点掌握SQL和Python基础\n- 多看社区里大神的经验分享\n\n### 第三阶段：面试冲刺\n- 每天模拟面试一次\n- 整理错题本反复回顾\n- 关注招聘市场动态\n\n祝大家都能找到满意的工作！",
    },
    {
        "title": "接口自动化测试框架搭建最佳实践",
        "category": "自动化测试",
        "tags": "接口测试,自动化,Python,Pytest",
        "is_essence": True,
        "is_top": False,
        "content": "最近在公司搭建了一套接口自动化测试框架，分享一下核心设计思路：\n\n### 框架分层\n1. **基础层**：封装Requests，统一处理日志、异常\n2. **业务层**：按业务模块组织API调用\n3. **数据层**：YAML/Excel驱动测试数据\n4. **用例层**：Pytest编写测试用例\n5. **报告层**：Allure生成美观报告\n\n### 核心技技巧\n- 使用conftest.py管理fixture\n- 环境变量隔离(dev/test/staging)\n- 用例间数据传递用pytest的cache\n- CI/CD集成Jenkins Pipeline\n\n有问题欢迎讨论！",
    },
    {
        "title": "面试必问：如何设计一个完整的测试方案？",
        "category": "面试经验",
        "tags": "面试,测试方案,设计方法",
        "is_essence": False,
        "is_top": False,
        "content": "最近面试了很多公司，几乎每家都会问这道题。分享一下我的答题模板：\n\n### 1. 测试范围\n明确被测对象、功能模块、不测范围\n\n### 2. 测试策略\n- 功能测试：等价类+边界值+场景法\n- 接口测试：正向+异常+边界\n- 性能测试：压测核心接口\n- 安全测试：SQL注入/XSS/越权\n\n### 3. 测试环境\n描述需要的测试环境配置\n\n### 4. 风险与应对\n识别高风险模块并给出预案\n\n### 5. 测试排期\n合理的时间安排\n\n记住要结合具体业务场景回答！",
    },
    {
        "title": "Selenium定位元素老是失败？试试这些方法",
        "category": "自动化测试",
        "tags": "Selenium,UI自动化,元素定位",
        "is_essence": False,
        "is_top": False,
        "content": 'Selenium元素定位失败是新手最常见的问题，总结几个原因和解决方案：\n\n### 常见原因\n1. 页面还没加载完就开始找元素 → 用显式等待\n2. 元素在iframe里 → 先切换iframe\n3. 动态ID每次不同 → 用css选择器部分匹配\n4. 元素被遮挡 → 用JS点击\n\n### 最佳实践\n```python\nfrom selenium.webdriver.support.ui import WebDriverWait\nfrom selenium.webdriver.support import expected_conditions as EC\n\nelement = WebDriverWait(driver, 10).until(\n    EC.presence_of_element_located((By.ID, "my-element"))\n)\n```\n\n显式等待永远比time.sleep靠谱！',
    },
    {
        "title": "性能测试入门：从JMeter到Locust",
        "category": "性能测试",
        "tags": "性能测试,JMeter,Locust,压力测试",
        "is_essence": False,
        "is_top": False,
        "content": "性能测试是测试工程师进阶的必经之路。分享一下我从JMeter到Locust的转变化：\n\n### JMeter\n- 优点：GUI操作简单，组件丰富，社区庞大\n- 缺点：Java编写扩展麻烦，报告不够美观\n\n### Locust  \n- 优点：Python脚本灵活，代码即配置，Web UI酷炫\n- 缺点：相对较新，部分企业不熟悉\n\n### 建议\n新手从JMeter开始，熟悉性能概念后转Locust写代码方式更高效。",
    },
    {
        "title": "测试工程师的日常工具清单",
        "category": "工具分享",
        "tags": "测试工具,效率,推荐",
        "is_essence": False,
        "is_top": False,
        "content": "整理了一份我日常使用的工具清单：\n\n| 类别 | 工具 | 用途 |\n|------|------|------|\n| 接口测试 | Postman/Apifox | 接口调试和文档 |\n| 抓包 | Charles/Fiddler | HTTP抓包分析 |\n| 数据库 | DBeaver/Navicat | 数据库管理 |\n| 代码 | VS Code/PyCharm | IDE |\n| 笔记 | Notion/语雀 | 知识管理 |\n| API | Swagger/Knife4j | 接口文档 |\n| CI/CD | Jenkins/GitLab CI | 持续集成 |\n\n欢迎补充！",
    },
    {
        "title": "SQL注入漏洞测试实战指南",
        "category": "安全测试",
        "tags": "安全测试,SQL注入,Web安全",
        "is_essence": True,
        "is_top": False,
        "content": "SQL注入是最古老但依然最常见的Web漏洞之一。完整的测试流程：\n\n### 1. 发现注入点\n```sql\n' OR '1'='1\n' OR '1'='1' --\nadmin'--\n```\n\n### 2. 判断注入类型\n- 数字型注入\n- 字符型注入\n- 搜索型注入\n\n### 3. 利用注入获取数据\n```sql\n' UNION SELECT 1,2,3--\n' UNION SELECT database(),user(),version()--\n```\n\n### 4. 使用SQLMap自动化\n```bash\nsqlmap -u \"http://target.com/page?id=1\" --dbs\n```\n\n安全测试务必在授权环境下进行！",
    },
    {
        "title": "两个月的求职之路，从自学到上岸",
        "category": "职业发展",
        "tags": "求职,面试,经验",
        "is_essence": False,
        "is_top": False,
        "content": "两个月前离职准备跳槽，今天终于拿到满意的Offer了。总结一下经验：\n\n### 时间线\n- 第一周：复习理论知识\n- 第二周：刷TestMaster题目\n- 第三周：准备项目经验\n- 第四周开始投简历面试\n- 第七周拿到Offer\n\n### 面试总结\n- 数据结构+算法题不多，但基础的要有\n- 重点考察测试思路和项目经验\n- SQL和Python是必考项\n- 自动化测试框架问得很深\n\n大家加油！",
    },
    {
        "title": "Git常用命令速查（测试工程师版）",
        "category": "工具分享",
        "tags": "Git,版本管理,命令",
        "is_essence": False,
        "is_top": False,
        "content": '测试工程师日常Git操作速查：\n\n```bash\n# 查看状态\ngit status\n\n# 拉取最新代码\ngit pull origin main\n\n# 创建并切换分支\ngit checkout -b feature/test-login\n\n# 提交代码\ngit add .\ngit commit -m "test: add login test cases"\n\n# 推送到远程\ngit push origin feature/test-login\n\n# 查看提交历史\ngit log --oneline -10\n\n# 回退\ngit reset --soft HEAD~1\n```\n\n收藏备用！',
    },
    {
        "title": "测试左移和测试右移，你了解多少？",
        "category": "测试基础",
        "tags": "测试左移,测试右移,质量保障",
        "is_essence": False,
        "is_top": False,
        "content": "测试左移和测试右移是现代质量保障的重要理念：\n\n### 测试左移\n把测试活动提前到开发的更早阶段：\n- 需求评审时参与\n- 设计阶段就考虑可测试性\n- 单元测试在开发阶段完成\n\n### 测试右移\n把测试活动延伸到生产环境：\n- 线上监控和告警\n- A/B测试\n- 混沌工程\n- 用户反馈收集\n\n两者结合形成全生命周期的质量保障体系。",
    },
]

COMMENTS = [
    {"content": "写得非常好！学习了", "like_count": 5},
    {
        "content": "作为一个刚入行的新人，这个帖子给了我很大帮助，感谢分享",
        "like_count": 12,
    },
    {"content": "能不能分享一下具体的学习计划表？", "like_count": 2},
    {"content": "我也是这么过来的，深有同感", "like_count": 3},
    {"content": "请问框架的代码可以开源吗？想学习一下", "like_count": 8},
    {"content": "已收藏，太实用了！", "like_count": 15},
    {"content": "补充一点：数据驱动推荐用pytest.mark.parametrize", "like_count": 6},
    {"content": "面试经验贴太及时了，下周正好有面试", "like_count": 4},
    {"content": "博主能出一个视频教程吗？", "like_count": 10},
    {"content": "写得清晰明了，点赞", "like_count": 3},
    {"content": "提个建议，可以和JUnit对比一下", "like_count": 1},
    {"content": "请问能不能具体讲讲性能瓶颈分析的方法？", "like_count": 7},
    {"content": "SQL注入测试建议加上时间盲注的内容", "like_count": 5},
    {"content": "好文，转发了", "like_count": 2},
    {"content": "学测试确实需要耐心，坚持就是胜利", "like_count": 9},
]

ACHIEVEMENTS = [
    {
        "key": "first_login",
        "name": "初次登录",
        "description": "完成首次登录",
        "icon": "🎉",
        "category": "入门",
        "threshold": 1,
        "exp_reward": 10,
    },
    {
        "key": "first_exercise",
        "name": "初次练习",
        "description": "完成第一道练习题",
        "icon": "✏️",
        "category": "练习",
        "threshold": 1,
        "exp_reward": 20,
    },
    {
        "key": "exercise_10",
        "name": "练习新手",
        "description": "完成10道练习题",
        "icon": "📝",
        "category": "练习",
        "threshold": 10,
        "exp_reward": 50,
    },
    {
        "key": "exercise_50",
        "name": "练习达人",
        "description": "完成50道练习题",
        "icon": "🏅",
        "category": "练习",
        "threshold": 50,
        "exp_reward": 100,
    },
    {
        "key": "exercise_100",
        "name": "练习专家",
        "description": "完成100道练习题",
        "icon": "👑",
        "category": "练习",
        "threshold": 100,
        "exp_reward": 200,
    },
    {
        "key": "first_checkin",
        "name": "初次签到",
        "description": "完成首次签到",
        "icon": "✅",
        "category": "签到",
        "threshold": 1,
        "exp_reward": 10,
    },
    {
        "key": "checkin_7",
        "name": "连续签到7天",
        "description": "连续签到7天",
        "icon": "🔥",
        "category": "签到",
        "threshold": 7,
        "exp_reward": 50,
    },
    {
        "key": "checkin_30",
        "name": "月度全勤",
        "description": "一个月内连续签到30天",
        "icon": "🌟",
        "category": "签到",
        "threshold": 30,
        "exp_reward": 150,
    },
    {
        "key": "first_exam",
        "name": "初次考试",
        "description": "完成首次考试",
        "icon": "📋",
        "category": "考试",
        "threshold": 1,
        "exp_reward": 30,
    },
    {
        "key": "exam_pass",
        "name": "考试通过",
        "description": "通过第一次考试",
        "icon": "🎊",
        "category": "考试",
        "threshold": 1,
        "exp_reward": 50,
    },
    {
        "key": "first_post",
        "name": "初入社区",
        "description": "发布第一篇帖子",
        "icon": "💬",
        "category": "社区",
        "threshold": 1,
        "exp_reward": 20,
    },
    {
        "key": "post_5",
        "name": "活跃成员",
        "description": "发布5篇帖子",
        "icon": "📢",
        "category": "社区",
        "threshold": 5,
        "exp_reward": 50,
    },
    {
        "key": "interview_complete",
        "name": "面试达人",
        "description": "完成10次模拟面试",
        "icon": "🎯",
        "category": "面试",
        "threshold": 10,
        "exp_reward": 100,
    },
    {
        "key": "leaderboard_top10",
        "name": "排行榜前十",
        "description": "进入排行榜前10名",
        "icon": "🏆",
        "category": "排名",
        "threshold": 1,
        "exp_reward": 200,
    },
]

EXAMS = [
    {
        "title": "软件测试基础综合测试",
        "description": "涵盖测试理论、测试方法、缺陷管理等基础知识",
        "exam_type": "模拟考试",
        "difficulty": "easy",
        "duration": 60,
        "total_score": 100,
        "pass_score": 60,
        "questions": [
            {
                "question_type": "single_choice",
                "content": "软件测试的目的是什么？",
                "options": '["A.证明程序没有错误","B.发现程序中的错误","C.改正程序中的错误","D.评估程序员的水平"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "软件测试的目的是发现错误，而不是证明没有错误。测试只能证明缺陷存在，不能证明缺陷不存在。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪个不属于黑盒测试方法？",
                "options": '["A.等价类划分","B.边界值分析","C.语句覆盖","D.因果图法"]',
                "correct_answer": "C",
                "score": 10,
                "analysis": "语句覆盖是白盒测试方法，关注代码内部的逻辑覆盖。",
            },
            {
                "question_type": "single_choice",
                "content": "V模型中，单元测试对应哪个开发阶段？",
                "options": '["A.需求分析","B.概要设计","C.详细设计","D.编码"]',
                "correct_answer": "D",
                "score": 10,
                "analysis": "V模型中左边是开发阶段，右边是对应的测试阶段：编码→单元测试，详细设计→集成测试，概要设计→系统测试，需求分析→验收测试。",
            },
            {
                "question_type": "single_choice",
                "content": "HTTP状态码404表示什么？",
                "options": '["A.服务器内部错误","B.请求的资源未找到","C.请求未授权","D.请求成功"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "404 Not Found表示服务器无法找到请求的资源。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪个是有效的等价类划分？",
                "options": '["A.将年龄1-100划分为1个有效等价类","B.将年龄1-100和101-200各划分为1个有效等价类（需求规定有效年龄为1-100）","C.不划分无效等价类","D.把有效等价类再细分"]',
                "correct_answer": "A",
                "score": 10,
                "analysis": "等价类划分中，1-100如果都是有效范围，可以作为一个有效等价类。",
            },
            {
                "question_type": "single_choice",
                "content": "性能测试指标TPS的含义是？",
                "options": '["A.每秒传输字节数","B.每秒处理事务数","C.总处理时间","D.测试通过率"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "TPS(Transactions Per Second)表示系统每秒能处理的事务数量。",
            },
            {
                "question_type": "single_choice",
                "content": "软件缺陷的严重程度应该由谁来决定？",
                "options": '["A.测试人员","B.开发人员","C.产品经理","D.测试人员和开发人员协商"]',
                "correct_answer": "D",
                "score": 10,
                "analysis": "缺陷严重程度应由测试人员和开发人员共同协商确定，综合考虑业务影响和技术实现。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪种说法关于回归测试是正确的？",
                "options": '["A.只执行一次","B.只测试新功能","C.验证修改后原有功能不受影响","D.不需要自动化"]',
                "correct_answer": "C",
                "score": 10,
                "analysis": "回归测试的目的是验证代码修改后，原有的功能没有受到负面影响。",
            },
            {
                "question_type": "single_choice",
                "content": "SQL注入攻击属于OWASP Top 10中的哪一类？",
                "options": '["A.失效的访问控制","B.注入(Injection)","C.安全配置错误","D.身份认证失效"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "SQL注入属于A03:2021-Injection注入类漏洞。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪个是最佳的自动化测试实践？",
                "options": '["A.所有测试用例都自动化","B.只自动化稳定的功能","C.从不维护自动化脚本","D.自动化替代手工测试"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "自动化测试适合稳定的、重复执行的功能。频繁变化的功能不适合过早自动化。",
            },
        ],
    },
    {
        "title": "接口测试能力评估",
        "description": "考察HTTP协议、RESTful API设计、接口测试工具等内容",
        "exam_type": "专项练习",
        "difficulty": "medium",
        "duration": 45,
        "total_score": 100,
        "pass_score": 70,
        "questions": [
            {
                "question_type": "single_choice",
                "content": "RESTful API中，获取资源的HTTP方法是？",
                "options": '["A.POST","B.GET","C.PUT","D.DELETE"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "RESTful规范中GET用于获取资源，POST用于创建，PUT用于更新，DELETE用于删除。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪个URL设计符合RESTful规范，用于获取用户ID为123的信息？",
                "options": '["A.GET /api/users/123","B.GET /api/getUser?id=123","C.POST /api/users/123","D.GET /api/user/123/info"]',
                "correct_answer": "A",
                "score": 10,
                "analysis": "RESTful风格使用资源名词+资源ID的URL模式，GET /users/123 是最佳实践。",
            },
            {
                "question_type": "single_choice",
                "content": "HTTP请求头Authorization通常用于什么？",
                "options": '["A.指定内容类型","B.身份认证","C.缓存控制","D.跨域请求"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "Authorization头用于携带认证信息，如Bearer Token等。",
            },
            {
                "question_type": "single_choice",
                "content": "Postman中，如何在URL中引用环境变量base_url？",
                "options": '["A.${base_url}","B.{{base_url}}","C.<base_url>","D.[base_url]"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "Postman使用双花括号{{variable_name}}语法引用变量。",
            },
            {
                "question_type": "single_choice",
                "content": "哪种请求方法不是幂等的？",
                "options": '["A.GET","B.PUT","C.DELETE","D.POST"]',
                "correct_answer": "D",
                "score": 10,
                "analysis": "POST不是幂等的，多次相同的POST请求会产生多个资源。GET、PUT、DELETE是幂等的。",
            },
            {
                "question_type": "single_choice",
                "content": "接口测试中，对必填参数不传值，属于什么测试？",
                "options": '["A.正向测试","B.异常测试","C.边界测试","D.性能测试"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "不传必填参数属于异常场景测试，验证系统的错误处理能力。",
            },
            {
                "question_type": "single_choice",
                "content": "Content-Type: application/json表示什么？",
                "options": '["A.请求体是HTML格式","B.请求体是JSON格式","C.请求体是XML格式","D.请求体是文本格式"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "Content-Type: application/json表示请求体使用JSON格式。",
            },
            {
                "question_type": "single_choice",
                "content": "HTTP状态码401和403的区别是？",
                "options": '["A.没有区别","B.401未认证，403无权限","C.401无权限，403未认证","D.401是客户端错误，403是服务端错误"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "401 Unauthorized表示未认证（需要登录），403 Forbidden表示已认证但无权限访问。",
            },
            {
                "question_type": "single_choice",
                "content": "在Pytest中，如何标记一个用例跳过执行？",
                "options": '["A.@pytest.mark.skip","B.@pytest.skip","C.@pytest.ignore","D.@pytest.mark.ignore"]',
                "correct_answer": "A",
                "score": 10,
                "analysis": "Pytest使用@pytest.mark.skip装饰器来跳过测试用例。",
            },
            {
                "question_type": "single_choice",
                "content": "接口测试中Mock的主要用途是？",
                "options": '["A.替代真实的接口","B.生成测试报告","C.管理测试用例","D.监控服务器性能"]',
                "correct_answer": "A",
                "score": 10,
                "analysis": "Mock主要用于模拟外部依赖的接口，使测试更加独立和稳定。",
            },
        ],
    },
    {
        "title": "Python编程能力测试",
        "description": "考察Python基础语法、数据结构、面向对象等知识",
        "exam_type": "模拟考试",
        "difficulty": "medium",
        "duration": 60,
        "total_score": 100,
        "pass_score": 60,
        "questions": [
            {
                "question_type": "single_choice",
                "content": "Python中，以下哪个数据类型是可变的？",
                "options": '["A.tuple","B.string","C.list","D.int"]',
                "correct_answer": "C",
                "score": 10,
                "analysis": "列表(list)是可变类型，元组(tuple)、字符串(string)、整数(int)都是不可变类型。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪个不是Python的关键字？",
                "options": '["A.def","B.class","C.function","D.return"]',
                "correct_answer": "C",
                "score": 10,
                "analysis": "Python中def用于定义函数，但没有function这个关键字。",
            },
            {
                "question_type": "single_choice",
                "content": "列表推导式 [x*2 for x in range(5)] 的结果是？",
                "options": '["A.[0,2,4,6,8]","B.[0,1,2,3,4]","C.[2,4,6,8,10]","D.[1,2,3,4,5]"]',
                "correct_answer": "A",
                "score": 10,
                "analysis": "range(5)生成[0,1,2,3,4]，每个元素乘以2得到[0,2,4,6,8]。",
            },
            {
                "question_type": "single_choice",
                "content": "Python中__init__方法的作用是什么？",
                "options": '["A.销毁对象","B.初始化对象","C.复制对象","D.比较对象"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "__init__是类的构造方法，在创建对象时自动调用来初始化对象属性。",
            },
            {
                "question_type": "single_choice",
                "content": "以下代码的输出是什么？\n```python\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(x)\n```",
                "options": '["A.[1, 2, 3]","B.[1, 2, 3, 4]","C.报错","D.[4, 1, 2, 3]"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "y = x 是引用赋值，y和x指向同一个列表对象，修改y也会影响x。",
            },
            {
                "question_type": "single_choice",
                "content": "Python中装饰器(decorator)的作用是？",
                "options": '["A.美化代码格式","B.在不修改原函数的情况下增加功能","C.加速代码执行","D.自动生成文档"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "装饰器是Python的一种设计模式，可以在不修改原函数的情况下增加额外的功能。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪种方式可以安全地打开文件？",
                "options": '["A.f = open(\\"file.txt\\")","B.with open(\\"file.txt\\") as f:","C.file.open(\\"file.txt\\")","D.open_file(\\"file.txt\\")"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "with语句可以确保文件在使用后正确关闭，即使发生异常也会关闭文件。",
            },
            {
                "question_type": "single_choice",
                "content": "Python包管理工具pip的全称是？",
                "options": '["A.Python Install Package","B.Pip Installs Packages","C.Python Index Package","D.Package Installer for Python"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "pip是一个递归缩写，Pip Installs Packages。",
            },
            {
                "question_type": "single_choice",
                "content": "以下哪个是正确的字典遍历方式？",
                "options": '["A.for k,v in dict.items()","B.for k in dict","C.for v in dict.values()","D.以上都正确"]',
                "correct_answer": "D",
                "score": 10,
                "analysis": "三种方式都正确：dict.items()遍历键值对，遍历dict本身得到键，dict.values()遍历值。",
            },
            {
                "question_type": "single_choice",
                "content": "Python中lambda函数的用途是？",
                "options": '["A.定义大型函数","B.创建匿名函数","C.替代所有函数","D.提升代码性能"]',
                "correct_answer": "B",
                "score": 10,
                "analysis": "lambda用于创建简短的匿名函数，常用于sorted、filter、map等高阶函数中。",
            },
        ],
    },
]

INTERVIEW_QUESTIONS = [
    {
        "title": "请介绍一下软件测试的生命周期', 'category': 'test_theory', 'difficulty': 'easy', 'tags': '测试理论,面试高频",
        "description": "简述软件测试生命周期(STLC)的各阶段', 'answer': '测试生命周期包括：需求分析→测试计划→测试设计→测试环境搭建→测试执行→缺陷管理→测试报告。每个阶段都有明确的输入、输出和准入准出标准。",
        "reference_solution": "测试生命周期包括：需求分析→测试计划→测试设计→测试环境搭建→测试执行→缺陷管理→测试报告。每个阶段都有明确的输入、输出和准入准出标准。",
    },
    {
        "title": "什么是等价类划分法？请举例说明', 'category': 'functional_test', 'difficulty': 'easy', 'tags': '测试方法,用例设计",
        "description": "解释等价类划分法的概念并给出实例', 'answer': '等价类划分是将输入域划分为若干等价类，从每个等价类中选取代表值进行测试。分为有效等价类和无效等价类。例如年龄输入框要求18-60，有效等价类：25(代表18-60)，无效等价类：10(代表<18)、70(代表>60)、abc(代表非数字)。",
        "reference_solution": "等价类划分是将输入域划分为若干等价类，从每个等价类中选取代表值进行测试。分为有效等价类和无效等价类。例如年龄输入框要求18-60，有效等价类：25(代表18-60)，无效等价类：10(代表<18)、70(代表>60)、abc(代表非数字)。",
    },
    {
        "title": "黑盒测试和白盒测试有什么区别？', 'category': 'test_theory', 'difficulty': 'easy', 'tags': '测试分类",
        "description": "对比黑盒测试和白盒测试', 'answer': '黑盒测试不考虑内部结构，只关注输入输出，方法包括等价类划分、边界值分析、因果图法等。白盒测试关注内部逻辑结构，需要了解代码，方法包括语句覆盖、判定覆盖、条件覆盖、路径覆盖等。",
        "reference_solution": "黑盒测试不考虑内部结构，只关注输入输出，方法包括等价类划分、边界值分析、因果图法等。白盒测试关注内部逻辑结构，需要了解代码，方法包括语句覆盖、判定覆盖、条件覆盖、路径覆盖等。",
    },
    {
        "title": "GET和POST请求的区别是什么？', 'category': 'api_test', 'difficulty': 'easy', 'tags': 'HTTP,接口测试",
        "description": "解释HTTP中GET和POST方法的主要区别', 'answer': '1.GET参数在URL中可见，POST参数在请求体中；2.GET有长度限制，POST没有；3.GET可被缓存/收藏，POST不能；4.GET是幂等的，POST不是；5.GET用于获取数据，POST用于提交数据。",
        "reference_solution": "1.GET参数在URL中可见，POST参数在请求体中；2.GET有长度限制，POST没有；3.GET可被缓存/收藏，POST不能；4.GET是幂等的，POST不是；5.GET用于获取数据，POST用于提交数据。",
    },
    {
        "title": "如何测试一个登录功能？请列出你的测试点', 'category': 'functional_test', 'difficulty': 'medium', 'tags': '功能测试,综合",
        "description": "设计登录功能的完整测试方案', 'answer': '功能测试：正确账号密码登录、错误密码、空用户名、空密码、特殊字符。安全测试：SQL注入、XSS、暴力破解、验证码。可用性测试：Tab键切换、回车提交、记住密码。兼容性：不同浏览器、不同设备。性能：高并发登录。",
        "reference_solution": "功能测试：正确账号密码登录、错误密码、空用户名、空密码、特殊字符。安全测试：SQL注入、XSS、暴力破解、验证码。可用性测试：Tab键切换、回车提交、记住密码。兼容性：不同浏览器、不同设备。性能：高并发登录。",
    },
    {
        "title": "请解释一下什么是持续集成(CI)和持续交付(CD)', 'category': 'devops', 'difficulty': 'medium', 'tags': 'DevOps,CI/CD",
        "description": "简述CI/CD的概念和实践意义', 'answer': 'CI(持续集成)是指开发人员频繁地将代码集成到主干，每次集成都通过自动化构建和测试来验证。CD(持续交付/部署)是在CI基础上，确保代码可以随时部署到生产环境。好处：快速发现集成问题、减少手工操作、提高交付效率。",
        "reference_solution": "CI(持续集成)是指开发人员频繁地将代码集成到主干，每次集成都通过自动化构建和测试来验证。CD(持续交付/部署)是在CI基础上，确保代码可以随时部署到生产环境。好处：快速发现集成问题、减少手工操作、提高交付效率。",
    },
    {
        "title": "你在自动化测试中遇到过什么问题？如何解决的？', 'category': 'automation_test', 'difficulty': 'medium', 'tags': '自动化测试,实战经验",
        "description": "分享自动化测试的实战经验', 'answer': '常见问题：1.元素定位失败→使用显式等待+多种定位策略；2.测试数据污染→每次测试前后清理数据；3.用例强依赖→设计独立可运行的用例；4.执行时间长→并行执行+合理分层；5.环境不稳定→容器化+环境隔离。",
        "reference_solution": "常见问题：1.元素定位失败→使用显式等待+多种定位策略；2.测试数据污染→每次测试前后清理数据；3.用例强依赖→设计独立可运行的用例；4.执行时间长→并行执行+合理分层；5.环境不稳定→容器化+环境隔离。",
    },
    {
        "title": "如何设计一个可维护的自动化测试框架？', 'category': 'automation_test', 'difficulty': 'hard', 'tags': '框架设计,架构",
        "description": "设计自动化测试框架的架构方案', 'answer': '分层架构：基础层(驱动封装)→数据层(测试数据管理)→业务层(页面对象/API封装)→用例层(测试用例)→报告层(测试报告)。关键原则：单一职责、开闭原则、依赖倒置。使用POM模式管理页面对象，使用数据驱动分离测试数据。",
        "reference_solution": "分层架构：基础层(驱动封装)→数据层(测试数据管理)→业务层(页面对象/API封装)→用例层(测试用例)→报告层(测试报告)。关键原则：单一职责、开闭原则、依赖倒置。使用POM模式管理页面对象，使用数据驱动分离测试数据。",
    },
    {
        "title": "性能测试中，TPS上不去可能是什么原因？', 'category': 'performance_test', 'difficulty': 'hard', 'tags': '性能测试,问题排查",
        "description": "分析性能瓶颈的可能原因', 'answer': '1.数据库连接池不够/慢SQL；2.应用服务器线程池不足；3.网络带宽瓶颈；4.代码中锁竞争；5.垃圾回收GC频繁；6.第三方接口响应慢；7.缺少缓存。排查思路：先看硬件(CPU/内存/网络)→再看中间件(连接池/线程池)→最后看代码。",
        "reference_solution": "1.数据库连接池不够/慢SQL；2.应用服务器线程池不足；3.网络带宽瓶颈；4.代码中锁竞争；5.垃圾回收GC频繁；6.第三方接口响应慢；7.缺少缓存。排查思路：先看硬件(CPU/内存/网络)→再看中间件(连接池/线程池)→最后看代码。",
    },
    {
        "title": "SQL注入漏洞的测试方法和防御措施？', 'category': 'security_test', 'difficulty': 'medium', 'tags': '安全测试,SQL注入",
        "description": "说明SQL注入的测试和防御', 'answer': '测试方法：输入单引号测试拼接错误→使用OR '1'='1测试绕过→使用UNION SELECT测试联合查询→使用SQLMap自动化测试。防御：1.使用参数化查询/预编译；2.输入校验和过滤；3.最小权限原则；4.WAF防护；5.避免详细错误信息暴露。",
        "reference_solution": "测试方法：输入单引号测试拼接错误→使用OR '1'='1测试绕过→使用UNION SELECT测试联合查询→使用SQLMap自动化测试。防御：1.使用参数化查询/预编译；2.输入校验和过滤；3.最小权限原则；4.WAF防护；5.避免详细错误信息暴露。",
    },
    {
        "title": "如何处理测试过程中的需求变更？', 'category': 'functional_test', 'difficulty': 'medium', 'tags': '测试管理,流程",
        "description": "分享需求变更下的测试应对策略', 'answer': '1.评估变更影响范围，更新测试计划；2.优先测试变更相关功能；3.执行完整的回归测试；4.更新测试用例和文档；5.与产品和开发保持及时沟通；6.合理安排测试优先级，确保核心功能不受影响。",
        "reference_solution": "1.评估变更影响范围，更新测试计划；2.优先测试变更相关功能；3.执行完整的回归测试；4.更新测试用例和文档；5.与产品和开发保持及时沟通；6.合理安排测试优先级，确保核心功能不受影响。",
    },
    {
        "title": "什么是Pytest的fixture？如何使用？', 'category': 'automation_test', 'difficulty': 'medium', 'tags': 'Pytest,Python",
        "description": "解释Pytest fixture的概念和用法', 'answer': 'Fixture是Pytest中用于测试前置准备和清理的机制。通过@pytest.fixture装饰器定义，在测试函数参数中引用。支持scope参数控制作用域(function/class/module/session)，支持yield实现teardown，支持conftest.py共享。比unittest的setUp/tearDown更灵活。",
        "reference_solution": "Fixture是Pytest中用于测试前置准备和清理的机制。通过@pytest.fixture装饰器定义，在测试函数参数中引用。支持scope参数控制作用域(function/class/module/session)，支持yield实现teardown，支持conftest.py共享。比unittest的setUp/tearDown更灵活。",
    },
    {
        "title": "JMeter中如何实现参数化？', 'category': 'performance_test', 'difficulty': 'medium', 'tags': 'JMeter,性能测试",
        "description": "说明JMeter参数化的实现方式', 'answer': '1.CSV Data Set Config：从CSV文件读取参数；2.用户定义的变量：在测试计划中定义固定变量；3.随机变量：使用Random Variable生成随机值；4.函数助手：__Random、__UUID等函数；5.正则表达式提取器：从响应中提取动态参数。",
        "reference_solution": "1.CSV Data Set Config：从CSV文件读取参数；2.用户定义的变量：在测试计划中定义固定变量；3.随机变量：使用Random Variable生成随机值；4.函数助手：__Random、__UUID等函数；5.正则表达式提取器：从响应中提取动态参数。",
    },
    {
        "title": "如何用Docker快速搭建测试环境？', 'category': 'devops', 'difficulty': 'medium', 'tags': 'Docker,测试环境",
        "description": "使用Docker搭建统一测试环境的方法', 'answer': '编写docker-compose.yml定义服务(应用+数据库+缓存等)，使用环境变量管理配置，通过volume持久化数据，使用network实现服务间通信。一键启动：docker-compose up -d。好处：环境一致性、快速部署、资源隔离、易于版本管理。",
        "reference_solution": "编写docker-compose.yml定义服务(应用+数据库+缓存等)，使用环境变量管理配置，通过volume持久化数据，使用network实现服务间通信。一键启动：docker-compose up -d。好处：环境一致性、快速部署、资源隔离、易于版本管理。",
    },
    {
        "title": "谈谈你对AI在软件测试中的应用前景的看法', 'category': 'ai_test', 'difficulty': 'hard', 'tags': 'AI测试,趋势",
        "description": "展望AI在测试领域的发展趋势', 'answer': 'AI在测试中的应用方向：1.智能测试用例生成(根据需求自动生成)；2.视觉回归测试(图像对比)；3.缺陷预测(根据代码变更预测高风险区域)；4.智能测试编排(优化测试执行顺序)；5.日志分析(自动识别异常模式)；6.测试报告自动生成。但AI不能完全替代人工测试的创造性和业务理解。",
        "reference_solution": "AI在测试中的应用方向：1.智能测试用例生成(根据需求自动生成)；2.视觉回归测试(图像对比)；3.缺陷预测(根据代码变更预测高风险区域)；4.智能测试编排(优化测试执行顺序)；5.日志分析(自动识别异常模式)；6.测试报告自动生成。但AI不能完全替代人工测试的创造性和业务理解。",
    },
]

AUTOTEST_GROUPS = [
    {"name": "用户模块", "description": "用户相关接口测试"},
    {"name": "订单模块", "description": "订单流程接口测试"},
    {"name": "商品模块", "description": "商品管理接口测试"},
]

AUTOTEST_CASES = [
    {
        "name": "用户登录', 'url': 'https://api.example.com/user/login', 'method': 'POST",
        "headers": '{"Content-Type": "application/json"}',
        "body": '{"username": "admin", "password": "123456"}',
        "description": "正常登录接口",
    },
    {
        "name": "获取用户信息', 'url': 'https://api.example.com/user/info', 'method': 'GET",
        "headers": '{"Authorization": "Bearer {{token}}"}',
        "body": None,
        "description": "获取当前登录用户信息",
    },
    {
        "name": "用户注册', 'url': 'https://api.example.com/user/register', 'method': 'POST",
        "headers": '{"Content-Type": "application/json"}',
        "body": '{"username": "newuser", "password": "123456", "email": "new@test.com"}',
        "description": "注册新用户",
    },
    {
        "name": "获取订单列表', 'url': 'https://api.example.com/order/list', 'method': 'GET",
        "headers": '{"Authorization": "Bearer {{token}}"}',
        "body": None,
        "description": "分页获取订单列表",
    },
    {
        "name": "创建订单', 'url': 'https://api.example.com/order/create', 'method': 'POST",
        "headers": '{"Content-Type": "application/json", "Authorization": "Bearer {{token}}"}',
        "body": '{"product_id": 1, "quantity": 2}',
        "description": "创建新订单",
    },
    {
        "name": "获取商品列表",
        "url": "https://api.example.com/product/list",
        "method": "GET",
        "headers": None,
        "body": None,
        "description": "获取所有商品",
    },
    {
        "name": "搜索商品', 'url': 'https://api.example.com/product/search', 'method': 'GET",
        "headers": None,
        "body": None,
        "description": "关键字搜索商品",
    },
    {
        "name": "添加购物车', 'url': 'https://api.example.com/cart/add', 'method': 'POST",
        "headers": '{"Content-Type": "application/json", "Authorization": "Bearer {{token}}"}',
        "body": '{"product_id": 1, "quantity": 1}',
        "description": "添加商品到购物车",
    },
]

ENVIRONMENTS = [
    {
        "name": "开发环境",
        "base_url": "https://dev-api.example.com",
        "variables": '{"env": "dev", "timeout": 30}',
        "is_default": False,
    },
    {
        "name": "测试环境",
        "base_url": "https://test-api.example.com",
        "variables": '{"env": "test", "timeout": 30}',
        "is_default": True,
    },
    {
        "name": "预发布环境",
        "base_url": "https://staging-api.example.com",
        "variables": '{"env": "staging", "timeout": 60}',
        "is_default": False,
    },
]

# ================================================================
# 主种子逻辑
# ================================================================


def random_date(days_back_min=1, days_back_max=30):
    days = random.randint(days_back_min, days_back_max)
    return datetime.now(timezone.utc) - timedelta(days=days, hours=random.randint(0, 23), minutes=random.randint(0, 59))


async def seed_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        stats = {}

        # --- 1. 用户 ---
        user_objects = []
        for u in USERS:
            existing = await session.execute(select(User).where(User.username == u["username"]))
            if existing.scalar_one_or_none():
                continue
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=AuthService.hash_password(u["password"]),
                is_admin=u["is_admin"],
                is_super_admin=u["is_super_admin"],
                avatar=u["avatar"],
                level=u["level"],
                score=u["score"],
                study_time=u["study_time"],
                created_at=random_date(60, 90),
            )
            session.add(user)
            user_objects.append(user)
        await session.flush()
        stats["users"] = len(user_objects)
        print(f"[OK] Users: {stats['users']} created")

        # --- 2. 社区帖子 ---
        post_objects = []
        for i, p in enumerate(POSTS):
            user = random.choice(user_objects) if user_objects else None
            if not user:
                continue
            post = Post(
                title=p["title"],
                content=p["content"],
                summary=p["content"][:100],
                tags=p["tags"],
                category=p["category"],
                view_count=random.randint(50, 500),
                like_count=random.randint(0, 50),
                comment_count=random.randint(0, 20),
                is_essence=p["is_essence"],
                is_top=p["is_top"],
                is_approved=True,
                user_id=user.id,
                created_at=random_date(0, 30),
            )
            session.add(post)
            post_objects.append(post)
        await session.flush()
        stats["posts"] = len(post_objects)
        print(f"[OK] Posts: {stats['posts']} created")

        # --- 3. 评论 ---
        comment_count = 0
        for post in post_objects:
            n = random.randint(1, 4)
            for c in random.sample(COMMENTS, min(n, len(COMMENTS))):
                user = random.choice(user_objects)
                comment = Comment(
                    content=c["content"],
                    like_count=random.randint(0, 8),
                    user_id=user.id,
                    post_id=post.id,
                    created_at=random_date(0, 20),
                )
                session.add(comment)
                comment_count += 1
        await session.flush()
        stats["comments"] = comment_count
        print(f"[OK] Comments: {stats['comments']} created")

        # --- 4. 点赞 ---
        like_count = 0
        for post in post_objects[:6]:
            for user in random.sample(user_objects, min(3, len(user_objects))):
                session.add(Like(user_id=user.id, post_id=post.id, created_at=random_date(1, 15)))
                like_count += 1
        stats["likes"] = like_count
        print(f"[OK] Likes: {stats['likes']} created")

        # --- 5. 成就 ---
        achievement_objects = []
        for a in ACHIEVEMENTS:
            existing = await session.execute(select(Achievement).where(Achievement.key == a["key"]))
            if existing.scalar_one_or_none():
                continue
            ach = Achievement(**a)
            session.add(ach)
            achievement_objects.append(ach)
        await session.flush()
        stats["achievements"] = len(achievement_objects)
        print(f"[OK] Achievements: {stats['achievements']} created")

        # --- 6. 用户成就 ---
        ua_count = 0
        for user in user_objects:
            n = random.randint(1, min(6, len(achievement_objects)))
            for ach in random.sample(achievement_objects, n):
                session.add(
                    UserAchievement(
                        user_id=user.id,
                        achievement_id=ach.id,
                        unlocked_at=random_date(0, 30),
                    )
                )
                ua_count += 1
        stats["user_achievements"] = ua_count
        print(f"[OK] User Achievements: {stats['user_achievements']} unlocked")

        # --- 7. 签到 ---
        checkin_count = 0
        for user in user_objects:
            streak = 0
            today = datetime.now(timezone.utc)
            for d in range(random.randint(3, 20)):
                checkin_date = today - timedelta(days=d + 1)
                streak += 1
                session.add(
                    DailyCheckin(
                        user_id=user.id,
                        checkin_date=checkin_date,
                        streak_count=streak,
                        exp_earned=random.choice([5, 10, 15, 20]),
                        created_at=checkin_date,
                    )
                )
                checkin_count += 1
        stats["checkins"] = checkin_count
        print(f"[OK] Checkins: {stats['checkins']} records")

        # --- 8. 考试 ---
        exam_objects = []
        for e in EXAMS:
            existing = await session.execute(select(Exam).where(Exam.title == e["title"]))
            if existing.scalar_one_or_none():
                continue
            questions_data = e.pop("questions")
            admin_user = next((u for u in user_objects if u.is_admin), user_objects[0])
            exam = Exam(
                **e,
                user_id=admin_user.id,
                is_published=True,
                start_time=random_date(10, 30),
            )
            session.add(exam)
            await session.flush()
            for qi, q in enumerate(questions_data):
                session.add(ExamQuestion(**q, exam_id=exam.id, sort_order=qi))
            exam_objects.append(exam)
        stats["exams"] = len(exam_objects)
        print(f"[OK] Exams: {stats['exams']} created")

        # --- 9. 面试题 ---
        interview_count = 0
        for iq in INTERVIEW_QUESTIONS:
            existing = await session.execute(select(InterviewQuestion).where(InterviewQuestion.title == iq["title"]))
            if existing.scalar_one_or_none():
                continue
            session.add(InterviewQuestion(**iq, is_published=True, view_count=random.randint(10, 200)))
            interview_count += 1
        stats["interview_questions"] = interview_count
        print(f"[OK] Interview Questions: {stats['interview_questions']} created")

        # --- 10. 自动化测试分组 ---
        group_objects = []
        for g in AUTOTEST_GROUPS:
            session.add(
                ApiGroup(
                    name=g["name"],
                    description=g["description"],
                    user_id=user_objects[0].id,
                )
            )
            group_objects.append(g)
        await session.flush()
        stats["autotest_groups"] = len(group_objects)
        print(f"[OK] AutoTest Groups: {stats['autotest_groups']} created")

        # --- 11. 环境 ---
        for env in ENVIRONMENTS:
            session.add(Environment(**env, user_id=user_objects[0].id))
        stats["environments"] = len(ENVIRONMENTS)
        print(f"[OK] Environments: {stats['environments']} created")

        # --- 12. 接口用例 ---
        case_count = 0
        for case in AUTOTEST_CASES:
            session.add(ApiCase(**case, user_id=user_objects[0].id, is_public=True))
            case_count += 1
        stats["autotest_cases"] = case_count
        print(f"[OK] AutoTest Cases: {stats['autotest_cases']} created")

        # --- 13. 学习进度 ---
        progress_count = 0
        exercises = (await session.execute(select(Exercise).limit(50))).scalars().all()
        for user in user_objects:
            n = random.randint(5, min(20, len(exercises)))
            for ex in random.sample(list(exercises), n):
                completed = random.random() > 0.3
                session.add(
                    Progress(
                        user_id=user.id,
                        exercise_id=ex.id,
                        completed=completed,
                        score=random.randint(60, 100) if completed else None,
                        time_spent=random.randint(2, 30),
                        attempts=random.randint(1, 3),
                        completed_at=random_date(0, 25) if completed else None,
                    )
                )
                progress_count += 1
        stats["progress"] = progress_count
        print(f"[OK] Progress: {stats['progress']} records")

        await session.commit()

        await _fix_code_exercises(session)
        stats["code_exercise_fixes"] = "applied"

        print("\n" + "=" * 60)
        print("[DONE] Seed Summary:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print("=" * 60)
        print("\nTest accounts (password: the same as username password field):")
        for u in USERS[:5]:
            print(f"  {u['username']} / {u['password']} ({'admin' if u['is_admin'] else 'user'})")
        print("  ... and more")


if __name__ == "__main__":
    print("=" * 60)
    print("[START] Seeding all TestMaster data...")
    print("=" * 60)
    asyncio.run(seed_all())


SQL_SETUP_DATA = {
    911: (
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, age INTEGER, city TEXT);"
        "INSERT INTO users VALUES (1,'张三','zhangsan@gmail.com',25,'北京');"
        "INSERT INTO users VALUES (2,'李四','lisi@163.com',30,'上海');"
        "INSERT INTO users VALUES (3,'王五','wangwu@qq.com',22,'广州');"
        "INSERT INTO users VALUES (4,'赵六','zhaoliu@gmail.com',28,'深圳');"
        "INSERT INTO users VALUES (5,'钱七','qianqi@outlook.com',35,'杭州');"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL, order_date TEXT);"
        "INSERT INTO orders VALUES (1,1,'笔记本电脑',5999.00,'2024-01-15');"
        "INSERT INTO orders VALUES (2,2,'手机',3999.00,'2024-02-20');"
        "INSERT INTO orders VALUES (3,1,'耳机',299.00,'2024-03-10');"
        "INSERT INTO orders VALUES (4,3,'平板',2999.00,'2024-04-05');"
        "INSERT INTO orders VALUES (5,2,'键盘',699.00,'2024-05-18');"
        "INSERT INTO orders VALUES (6,4,'显示器',2499.00,'2024-06-22');"
        "INSERT INTO orders VALUES (7,5,'鼠标',199.00,'2024-07-30');"
        "INSERT INTO orders VALUES (8,3,'摄像头',499.00,'2024-08-14');"
    ),
    912: (
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, age INTEGER);"
        "INSERT INTO users VALUES (1,'张三','zhangsan@gmail.com',25);"
        "INSERT INTO users VALUES (2,'李四','lisi@163.com',30);"
        "INSERT INTO users VALUES (3,'王五','wangwu@qq.com',22);"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL, order_date TEXT);"
        "INSERT INTO orders VALUES (1,1,'笔记本电脑',5999.00,'2024-01-15');"
        "INSERT INTO orders VALUES (2,2,'手机',3999.00,'2024-02-20');"
        "INSERT INTO orders VALUES (3,1,'耳机',299.00,'2024-03-10');"
        "INSERT INTO orders VALUES (4,3,'平板',2999.00,'2024-04-05');"
        "INSERT INTO orders VALUES (5,2,'键盘',699.00,'2024-05-18');"
    ),
    913: (
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, username TEXT, product TEXT, amount REAL, order_date TEXT);"
        "INSERT INTO orders VALUES (1,'张三','笔记本电脑',5999.00,'2024-01-15');"
        "INSERT INTO orders VALUES (2,'李四','手机',3999.00,'2024-02-20');"
        "INSERT INTO orders VALUES (3,'张三','耳机',299.00,'2024-03-10');"
        "INSERT INTO orders VALUES (4,'王五','平板',2999.00,'2024-04-05');"
        "INSERT INTO orders VALUES (5,'李四','键盘',699.00,'2024-05-18');"
        "INSERT INTO orders VALUES (6,'张三','显示器',2499.00,'2024-06-22');"
    ),
    914: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL, hire_date TEXT);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00,'2022-01-15');"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00,'2022-03-20');"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00,'2021-06-10');"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00,'2023-02-01');"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00,'2020-08-15');"
        "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT, budget REAL);"
        "INSERT INTO departments VALUES (1,'技术部',500000.00);"
        "INSERT INTO departments VALUES (2,'市场部',300000.00);"
        "INSERT INTO departments VALUES (3,'人事部',200000.00);"
    ),
    1041: (
        "CREATE TABLE scores (id INTEGER PRIMARY KEY, name TEXT, score REAL, subject TEXT);"
        "INSERT INTO scores VALUES (1,'张三',85.5,'数学');"
        "INSERT INTO scores VALUES (2,'李四',92.0,'数学');"
        "INSERT INTO scores VALUES (3,'王五',78.5,'数学');"
        "INSERT INTO scores VALUES (4,'赵六',95.0,'数学');"
        "INSERT INTO scores VALUES (5,'钱七',88.0,'数学');"
    ),
    1042: (
        "CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, amount REAL, sale_date TEXT, region TEXT);"
        "INSERT INTO sales VALUES (1,'手机',3999.00,'2024-01-15','华东');"
        "INSERT INTO sales VALUES (2,'电脑',5999.00,'2024-01-20','华北');"
        "INSERT INTO sales VALUES (3,'耳机',299.00,'2024-02-10','华东');"
        "INSERT INTO sales VALUES (4,'平板',2999.00,'2024-02-15','华南');"
        "INSERT INTO sales VALUES (5,'手机',3999.00,'2024-03-01','华北');"
    ),
    1043: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL, hire_date TEXT);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00,'2022-01-15');"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00,'2022-03-20');"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00,'2021-06-10');"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00,'2023-02-01');"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00,'2020-08-15');"
    ),
    1044: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00);"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00);"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00);"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00);"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00);"
    ),
    1045: (
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, stock INTEGER);"
        "INSERT INTO products VALUES (1,'手机','电子',3999.00,100);"
        "INSERT INTO products VALUES (2,'电脑','电子',5999.00,50);"
        "INSERT INTO products VALUES (3,'耳机','电子',299.00,200);"
        "INSERT INTO products VALUES (4,'T恤','服装',99.00,500);"
        "INSERT INTO products VALUES (5,'牛仔裤','服装',199.00,300);"
    ),
    1046: (
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);"
        "INSERT INTO products VALUES (1,'苹果手机','电子',3999.00);"
        "INSERT INTO products VALUES (2,'联想电脑','电子',5999.00);"
        "INSERT INTO products VALUES (3,'索尼耳机','电子',299.00);"
        "INSERT INTO products VALUES (4,'耐克T恤','服装',99.00);"
        "INSERT INTO products VALUES (5,'李维斯牛仔裤','服装',199.00);"
    ),
    1047: (
        "CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, amount REAL, sale_date TEXT);"
        "INSERT INTO sales VALUES (1,'手机',3999.00,'2024-01-15');"
        "INSERT INTO sales VALUES (2,'电脑',5999.00,'2024-02-20');"
        "INSERT INTO sales VALUES (3,'耳机',299.00,'2024-03-10');"
        "INSERT INTO sales VALUES (4,'平板',2999.00,'2024-04-05');"
        "INSERT INTO sales VALUES (5,'键盘',699.00,'2024-05-18');"
    ),
    1048: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL, level INTEGER);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00,5);"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00,3);"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00,7);"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00,2);"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00,8);"
    ),
    1049: (
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, age INTEGER);"
        "INSERT INTO users VALUES (1,'张三',25);"
        "INSERT INTO users VALUES (2,'李四',30);"
        "INSERT INTO users VALUES (3,'王五',22);"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL);"
        "INSERT INTO orders VALUES (1,1,'笔记本电脑',5999.00);"
        "INSERT INTO orders VALUES (2,2,'手机',3999.00);"
        "INSERT INTO orders VALUES (3,1,'耳机',299.00);"
        "INSERT INTO orders VALUES (4,3,'平板',2999.00);"
        "INSERT INTO orders VALUES (5,2,'键盘',699.00);"
    ),
    1050: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00);"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00);"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00);"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00);"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00);"
    ),
    1051: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL, level INTEGER);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00,5);"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00,3);"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00,7);"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00,2);"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00,8);"
    ),
    1052: (
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, stock INTEGER);"
        "INSERT INTO products VALUES (1,'手机','电子',3999.00,100);"
        "INSERT INTO products VALUES (2,'电脑','电子',5999.00,50);"
        "INSERT INTO products VALUES (3,'耳机','电子',299.00,0);"
        "INSERT INTO products VALUES (4,'T恤','服装',99.00,500);"
        "INSERT INTO products VALUES (5,'牛仔裤','服装',199.00,NULL);"
    ),
    1053: (
        "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL);"
        "INSERT INTO employees VALUES (1,'张三','技术部',15000.00);"
        "INSERT INTO employees VALUES (2,'李四','市场部',12000.00);"
        "INSERT INTO employees VALUES (3,'王五','技术部',18000.00);"
        "INSERT INTO employees VALUES (4,'赵六','人事部',10000.00);"
        "INSERT INTO employees VALUES (5,'钱七','技术部',20000.00);"
    ),
    1054: (
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, stock INTEGER);"
        "INSERT INTO products VALUES (1,'手机','电子',3999.00,100);"
        "INSERT INTO products VALUES (2,'电脑','电子',5999.00,50);"
        "INSERT INTO products VALUES (3,'耳机','电子',299.00,200);"
        "INSERT INTO products VALUES (4,'T恤','服装',99.00,500);"
        "INSERT INTO products VALUES (5,'牛仔裤','服装',199.00,300);"
    ),
    1055: (
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, age INTEGER, city TEXT);"
        "INSERT INTO users VALUES (1,'张三',25,'北京');"
        "INSERT INTO users VALUES (2,'李四',30,'上海');"
        "INSERT INTO users VALUES (3,'王五',22,'广州');"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL);"
        "INSERT INTO orders VALUES (1,1,'笔记本电脑',5999.00);"
        "INSERT INTO orders VALUES (2,2,'手机',3999.00);"
        "INSERT INTO orders VALUES (3,1,'耳机',299.00);"
        "INSERT INTO orders VALUES (4,3,'平板',2999.00);"
        "INSERT INTO orders VALUES (5,2,'键盘',699.00);"
    ),
}

SQL_CODE_TEMPLATES = {
    911: "-- 请在此编写SQL查询\nSELECT ... FROM ... WHERE ...;",
    912: "-- 请使用JOIN连接查询\nSELECT ... FROM ... JOIN ... ON ...;",
    913: "-- 请使用GROUP BY和HAVING完成分组统计\nSELECT ..., ...(...) as ..., ...(...) as ... FROM orders GROUP BY ... HAVING ...(...) > ... ORDER BY ... DESC;",
    914: "-- 请使用子查询查找满足条件的员工\nSELECT ... FROM employees WHERE ... > (SELECT ...(...) FROM ...);",
    1041: "-- 请编写排序和筛选SQL\nSELECT ... FROM ... WHERE ... ORDER BY ...;",
    1042: "-- 请使用CTE(通用表表达式)查询\nWITH ... AS (...) SELECT ... FROM ...;",
    1043: "-- 请查询满足条件的员工记录\nSELECT ... FROM employees WHERE ...;",
    1044: "-- 请使用子查询查找满足条件的员工\nSELECT ... FROM employees WHERE ... > (SELECT ...(...) FROM ...);",
    1045: "-- 请按分类统计商品总价值\nSELECT ..., ...(... * ...) as ... FROM products GROUP BY ...;",
    1046: "-- 请使用字符串函数处理商品名称\nSELECT ...(...), ...(...) FROM products;",
    1047: "-- 请查询指定日期之后的销售记录\nSELECT ... FROM sales WHERE ... >= '...';",
    1048: "-- 请使用CASE条件查询\nSELECT ..., CASE WHEN ... THEN ... ELSE ... END as ... FROM employees;",
    1049: "-- 请使用多表JOIN查询\nSELECT ... FROM ... JOIN ... ON ...;",
    1050: "-- 请查询指定部门的员工\nSELECT ... FROM employees WHERE ... = ...;",
    1051: "-- 请查询指定级别及以上的员工\nSELECT ... FROM employees WHERE ... >= ...;",
    1052: "-- 请查询有库存的商品并按价格排序\nSELECT ... FROM products WHERE ... > 0 ORDER BY ...;",
    1053: "-- 请查询薪资最高的前N名员工\nSELECT ... FROM employees ORDER BY ... DESC LIMIT ...;",
    1054: "-- 请查询指定分类的商品\nSELECT ... FROM products WHERE ... = '...';",
    1055: "-- 请编写连接查询\nSELECT ... FROM ... JOIN ... ON ...;",
}


async def _fix_code_exercises(session):
    print("\n[STEP] 修复代码题数据...")
    from sqlalchemy import text as sql_text

    result = await session.execute(
        sql_text("SELECT id, language, exercise_type FROM exercises WHERE exercise_type = 'code'")
    )
    code_exercises = result.fetchall()

    sql_fixed = 0
    python_fixed = 0

    for row in code_exercises:
        eid, lang, etype = row

        if lang and lang.lower() == "sql":
            if eid in SQL_SETUP_DATA:
                await session.execute(
                    sql_text(
                        "UPDATE exercises SET setup_sql = :sql WHERE id = :id AND (setup_sql IS NULL OR setup_sql = '')"
                    ),
                    {"sql": SQL_SETUP_DATA[eid], "id": eid},
                )
            if eid in SQL_CODE_TEMPLATES:
                await session.execute(
                    sql_text(
                        "UPDATE exercises SET code_template = :tpl WHERE id = :id AND (code_template IS NULL OR code_template = '' OR code_template = solution)"
                    ),
                    {"tpl": SQL_CODE_TEMPLATES[eid], "id": eid},
                )
            sql_fixed += 1

        elif lang and lang.lower() == "python":
            await session.execute(
                sql_text(
                    "UPDATE exercises SET test_cases = NULL WHERE id = :id AND test_cases IS NOT NULL AND test_cases != '' AND test_cases NOT LIKE '[%'"
                ),
                {"id": eid},
            )
            result2 = await session.execute(
                sql_text("SELECT solution FROM exercises WHERE id = :id"),
                {"id": eid},
            )
            sol_row = result2.fetchone()
            if sol_row and sol_row[0]:
                sol = sol_row[0]
                tpl = _generate_python_template(sol)
                if tpl:
                    await session.execute(
                        sql_text(
                            "UPDATE exercises SET code_template = :tpl WHERE id = :id AND (code_template IS NULL OR code_template = '')"
                        ),
                        {"tpl": tpl, "id": eid},
                    )
            python_fixed += 1

    await session.commit()
    print(f"  [OK] SQL题修复: {sql_fixed} 道")
    print(f"  [OK] Python题修复: {python_fixed} 道")


def _generate_python_template(solution: str) -> str:
    import re

    lines = solution.strip().split("\n")
    template_lines = []
    in_function = False
    in_class = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("def "):
            sig = re.sub(r":\s*$", "", stripped)
            template_lines.append(line[: len(line) - len(line.lstrip())] + sig + ":")
            indent = line[: len(line) - len(line.lstrip())]
            template_lines.append(indent + "    # TODO: 在此写代码")
            template_lines.append(indent + "    pass")
            in_function = True
            continue

        if stripped.startswith("class "):
            sig = re.sub(r":\s*$", "", stripped)
            template_lines.append(line[: len(line) - len(line.lstrip())] + sig + ":")
            in_class = True
            continue

        if stripped.startswith("import ") or stripped.startswith("from "):
            template_lines.append(line)
            continue

        if stripped.startswith('"""') or stripped.startswith("'''"):
            template_lines.append(line)
            continue

        if not in_function and not in_class and stripped and not stripped.startswith("#"):
            template_lines.append("# TODO: 在此写代码")
            break

    if not template_lines:
        return "# TODO: 在此写代码\npass"

    return "\n".join(template_lines)
