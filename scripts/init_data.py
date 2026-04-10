# Initialize database with sample data
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.app import create_app
from backend.extensions import db
from backend.models.models import LearningPath, Exercise, User, InterviewQuestion
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("Creating tables...")
    db.create_all()
    
    # Check if data already exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("Creating admin user...")
        admin_user = User(
            username='admin',
            email='admin@testmaster.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()
    
    # Clear existing data for fresh initialization
    print("Clearing existing learning paths and exercises...")
    Exercise.query.delete()
    LearningPath.query.delete()
    db.session.commit()
    
    print("Creating test engineer learning paths...")
    
    # 阶段1：测试入门筑基
    stage1_paths = [
        LearningPath(
            title='软件测试基础理论',
            description='软件测试入门必备，掌握测试基础概念、原则、模型和流程，建立测试思维。',
            language='通用',
            difficulty='beginner',
            stage=1,
            estimated_hours=20,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='测试用例设计方法',
            description='掌握常用的测试用例设计方法，包括黑盒测试和白盒测试的各种设计技巧。',
            language='通用',
            difficulty='beginner',
            stage=1,
            estimated_hours=15,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='计算机基础与SQL入门',
            description='测试工程师必备的计算机基础、网络基础和数据库SQL基础技能。',
            language='通用',
            difficulty='beginner',
            stage=1,
            estimated_hours=25,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='测试工具基础',
            description='掌握测试工程师常用的基础工具，包括测试管理工具、缺陷管理工具、文档工具等。',
            language='通用',
            difficulty='beginner',
            stage=1,
            estimated_hours=10,
            is_public=True,
            user_id=admin_user.id
        )
    ]
    
    # 阶段2：功能测试精通
    stage2_paths = [
        LearningPath(
            title='Web端功能测试实战',
            description='掌握Web端项目的功能测试方法、要点和实战技巧，能独立完成Web项目测试。',
            language='通用',
            difficulty='beginner',
            stage=2,
            estimated_hours=30,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='APP端功能测试实战',
            description='掌握APP端测试要点，包括安装、兼容性、中断、性能等专项测试。',
            language='通用',
            difficulty='beginner',
            stage=2,
            estimated_hours=35,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='小程序与H5测试',
            description='掌握微信小程序、H5页面的测试要点和常见问题。',
            language='通用',
            difficulty='beginner',
            stage=2,
            estimated_hours=15,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='测试流程与项目实战',
            description='完整的测试项目实战，从需求分析到测试报告输出的全流程演练。',
            language='通用',
            difficulty='intermediate',
            stage=2,
            estimated_hours=40,
            is_public=True,
            user_id=admin_user.id
        )
    ]
    
    # 阶段3：测试技术进阶
    stage3_paths = [
        LearningPath(
            title='接口测试入门到精通',
            description='掌握接口测试基础、HTTP协议、Postman/Jmeter等工具使用，能独立完成接口测试。',
            language='通用',
            difficulty='intermediate',
            stage=3,
            estimated_hours=40,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='Linux与Shell脚本',
            description='测试工程师必备的Linux技能，常用命令、Shell脚本编写、日志排查。',
            language='Linux',
            difficulty='intermediate',
            stage=3,
            estimated_hours=30,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='数据库进阶与测试',
            description='SQL高级查询、数据库事务、索引、存储过程，以及数据库测试方法。',
            language='SQL',
            difficulty='intermediate',
            stage=3,
            estimated_hours=25,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='性能测试基础',
            description='性能测试基础概念、指标、Jmeter基础使用，能完成简单的性能压测。',
            language='通用',
            difficulty='intermediate',
            stage=3,
            estimated_hours=30,
            is_public=True,
            user_id=admin_user.id
        )
    ]
    
    # 阶段4：自动化测试专家
    stage4_paths = [
        LearningPath(
            title='Python编程入门到精通',
            description='自动化测试必备的Python编程技能，从基础语法到面向对象编程。',
            language='Python',
            difficulty='intermediate',
            stage=4,
            estimated_hours=50,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='接口自动化测试框架开发',
            description='使用Python+Requests+Pytest开发企业级接口自动化测试框架。',
            language='Python',
            difficulty='advanced',
            stage=4,
            estimated_hours=60,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='UI自动化测试(Selenium)',
            description='Web UI自动化测试，Selenium高级使用、PageObject设计模式、框架开发。',
            language='Python',
            difficulty='advanced',
            stage=4,
            estimated_hours=50,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='APP自动化测试(Appium)',
            description='APP自动化测试，Appium使用、多设备并发测试、自动化框架开发。',
            language='Python',
            difficulty='advanced',
            stage=4,
            estimated_hours=45,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='性能测试进阶与调优',
            description='性能测试场景设计、Jmeter高级使用、性能监控与瓶颈分析调优。',
            language='通用',
            difficulty='advanced',
            stage=4,
            estimated_hours=55,
            is_public=True,
            user_id=admin_user.id
        )
    ]
    
    # 阶段5：测试架构师之路
    stage5_paths = [
        LearningPath(
            title='测试平台开发',
            description='前后端开发基础，测试平台架构设计与开发实战。',
            language='Python+Vue',
            difficulty='advanced',
            stage=5,
            estimated_hours=80,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='DevOps与CI/CD集成',
            description='持续集成/持续交付，自动化测试融入DevOps流程，Jenkins实战。',
            language='通用',
            difficulty='advanced',
            stage=5,
            estimated_hours=40,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='质量体系建设',
            description='质量度量体系、测试流程优化、测试效能提升、质量文化建设。',
            language='通用',
            difficulty='advanced',
            stage=5,
            estimated_hours=50,
            is_public=True,
            user_id=admin_user.id
        ),
        LearningPath(
            title='专项测试技术',
            description='安全测试、移动专项测试、大数据测试、云原生测试等高级专项技术。',
            language='通用',
            difficulty='advanced',
            stage=5,
            estimated_hours=70,
            is_public=True,
            user_id=admin_user.id
        )
    ]
    
    # 添加所有学习路径
    all_paths = stage1_paths + stage2_paths + stage3_paths + stage4_paths + stage5_paths
    for path in all_paths:
        db.session.add(path)
    
    db.session.commit()
    print(f"Created {len(all_paths)} learning paths!")
    
    # 创建样例习题
    print("Creating sample exercises...")
    
    # 阶段1基础理论题
    stage1_exercises = [
        Exercise(
            title='软件测试的目的是什么？',
            description='请简述软件测试的核心目的和价值。',
            instructions='请用自己的话描述软件测试的目的，不少于3个要点。',
            solution='软件测试的目的包括：1. 发现软件中的缺陷和问题；2. 评估软件的质量和风险；3. 保证软件满足用户需求和预期；4. 预防缺陷，提升开发过程质量。',
            difficulty='easy',
            language='通用',
            category='测试基础',
            stage=1,
            knowledge_point='软件测试基础概念',
            time_estimate=5,
            is_public=True,
            user_id=admin_user.id
        ),
        Exercise(
            title='什么是黑盒测试？什么是白盒测试？',
            description='请解释黑盒测试和白盒测试的概念和区别。',
            instructions='分别解释两种测试方法，说明它们的适用场景和特点。',
            solution='黑盒测试：不关注内部实现，只关注输入输出是否符合需求，适用于功能测试、集成测试、系统测试等。白盒测试：关注内部代码实现逻辑，对代码的路径、分支、条件等进行测试，适用于单元测试。',
            difficulty='easy',
            language='通用',
            category='测试基础',
            stage=1,
            knowledge_point='测试方法分类',
            time_estimate=8,
            is_public=True,
            user_id=admin_user.id
        )
    ]
    
    # 代码练习题
    code_exercises = [
        Exercise(
            title='Python Hello World',
            description='编写一个Python程序，输出"Hello World!"',
            instructions='使用print函数输出字符串，注意大小写和标点符号。',
            solution='print("Hello World!")',
            difficulty='easy',
            language='Python',
            category='代码练习',
            stage=1,
            knowledge_point='Python基础语法',
            time_estimate=5,
            is_public=True,
            user_id=admin_user.id,
            exercise_type='code',
            code_template='# 编写代码输出Hello World!\nprint("Hello World!")',
            expected_output='Hello World!'
        ),
        Exercise(
            title='SQL查询学生表',
            description='有一个学生表student(id, name, age, class_id)，请查询所有年龄大于18岁的学生姓名。',
            instructions='写出对应的SQL查询语句。',
            solution='SELECT name FROM student WHERE age > 18;',
            difficulty='easy',
            language='SQL',
            category='代码练习',
            stage=1,
            knowledge_point='SQL查询基础',
            time_estimate=3,
            is_public=True,
            user_id=admin_user.id,
            exercise_type='code',
            code_template='-- 查询年龄大于18岁的学生姓名\nSELECT name FROM student WHERE age > 18;',
            expected_output='返回所有符合条件的学生姓名'
        ),
        Exercise(
            title='Python计算1到100的和',
            description='编写Python代码，计算1到100所有整数的和。',
            instructions='可以使用for循环或者sum函数实现。',
            solution='total = sum(range(1, 101))\nprint(total)',
            difficulty='easy',
            language='Python',
            category='代码练习',
            stage=1,
            knowledge_point='Python循环和函数',
            time_estimate=10,
            is_public=True,
            user_id=admin_user.id,
            exercise_type='code',
            code_template='# 计算1到100的和\ntotal = 0\nfor i in range(1, 101):\n    total += i\nprint(total)',
            expected_output='5050'
        ),
        Exercise(
            title='SQL统计班级人数',
            description='学生表student包含字段class_id(班级ID)，请统计每个班级的学生人数。',
            instructions='使用GROUP BY分组查询。',
            solution='SELECT class_id, COUNT(*) as student_count FROM student GROUP BY class_id;',
            difficulty='medium',
            language='SQL',
            category='代码练习',
            stage=1,
            knowledge_point='SQL分组查询',
            time_estimate=8,
            is_public=True,
            user_id=admin_user.id,
            exercise_type='code',
            code_template='-- 统计每个班级的学生人数\nSELECT class_id, COUNT(*) as student_count \nFROM student \nGROUP BY class_id;',
            expected_output='每个班级ID和对应的学生人数'
        ),
        Exercise(
            title='Python判断回文字符串',
            description='编写一个Python函数，判断输入的字符串是否是回文字符串（正读和反读都一样）。',
            instructions='忽略大小写和非字母数字字符。',
            solution='def is_palindrome(s):\n    s = \'\'.join(c.lower() for c in s if c.isalnum())\n    return s == s[::-1]\n\n# 测试\nprint(is_palindrome("A man, a plan, a canal: Panama"))  # True\nprint(is_palindrome("race a car"))  # False',
            difficulty='medium',
            language='Python',
            category='代码练习',
            stage=2,
            knowledge_point='Python字符串处理',
            time_estimate=15,
            is_public=True,
            user_id=admin_user.id,
            exercise_type='code',
            code_template='def is_palindrome(s):\n    # 在这里编写代码\n    pass\n\n# 测试\nprint(is_palindrome("A man, a plan, a canal: Panama"))',
            expected_output='True\nFalse'
        )
    ]
    
    # 添加基础习题
    for ex in stage1_exercises:
        db.session.add(ex)
    
    # 添加代码习题
    for ex in code_exercises:
        db.session.add(ex)
    
    db.session.commit()
    print(f"Created {len(stage1_exercises) + len(code_exercises)} sample exercises!")
    
    print("All data initialized successfully!")
    print("\nSummary:")
    print(f"- 阶段1（测试入门）：{len(stage1_paths)}个学习路径")
    print(f"- 阶段2（功能测试）：{len(stage2_paths)}个学习路径")
    print(f"- 阶段3（技术进阶）：{len(stage3_paths)}个学习路径")
    print(f"- 阶段4（自动化测试）：{len(stage4_paths)}个学习路径")
    print(f"- 阶段5（测试架构师）：{len(stage5_paths)}个学习路径")
    print(f"- 总计：{len(all_paths)}个学习路径，{len(stage1_exercises) + len(code_exercises)}个习题")
    
    # 初始化面试题
    print("\nInitializing interview questions...")
    interview_questions = [
        # 基础测试
        {
            "title": "什么是软件测试？软件测试的目的是什么？",
            "answer": """软件测试是在规定的条件下对程序进行操作，以发现程序错误，衡量软件质量，并对其是否能满足设计要求进行评估的过程。

软件测试的目的：
1. 发现软件中存在的缺陷和错误
2. 验证软件是否满足用户需求和功能规格
3. 评估软件的质量和可靠性
4. 为软件上线和发布提供质量保证
5. 预防缺陷，降低软件在使用过程中的风险

好的测试用例是发现了至今尚未发现的错误的测试。""",
            "category": "基础测试",
            "difficulty": "easy",
            "position_level": "初级",
            "tags": "测试基础,软件测试概念",
            "company": "通用"
        },
        {
            "title": "请解释什么是黑盒测试和白盒测试？它们的区别是什么？",
            "answer": """黑盒测试（功能测试）：
- 不考虑程序内部结构和实现逻辑
- 只关注软件的功能是否符合需求规格
- 主要用于系统测试和验收测试
- 常用方法：等价类划分、边界值分析、错误推测法、因果图等

白盒测试（结构测试）：
- 关注程序内部结构和代码实现
- 对程序的逻辑路径进行覆盖测试
- 主要用于单元测试和集成测试
- 常用覆盖标准：语句覆盖、判定覆盖、条件覆盖、判定/条件覆盖、路径覆盖等

主要区别：
1. 测试对象不同：黑盒测试关注功能，白盒测试关注代码结构
2. 测试依据不同：黑盒测试依据需求规格，白盒测试依据代码逻辑
3. 测试方法不同：黑盒测试用例基于功能设计，白盒测试用例基于代码逻辑设计
4. 适用阶段不同：黑盒测试主要在后期，白盒测试主要在前期""",
            "category": "基础测试",
            "difficulty": "medium",
            "position_level": "初级",
            "tags": "测试方法,黑盒测试,白盒测试",
            "company": "字节跳动"
        },
        {
            "title": "请描述软件测试的生命周期？",
            "answer": """软件测试生命周期（STLC）包括以下阶段：
1. 需求分析阶段：分析需求，确定测试范围和重点
2. 测试计划阶段：制定测试计划，包括测试策略、资源、进度、风险等
3. 测试设计阶段：编写测试用例，准备测试数据和测试环境
4. 测试执行阶段：执行测试用例，记录缺陷，跟踪缺陷修复
5. 测试评估阶段：评估测试结果，分析测试覆盖率，输出测试报告
6. 测试收尾阶段：测试总结，经验沉淀，测试资产归档

每个阶段都有明确的输入输出和准入准出标准，保证测试过程的可控和质量。""",
            "category": "基础测试",
            "difficulty": "medium",
            "position_level": "初级",
            "tags": "测试流程,测试生命周期",
            "company": "阿里巴巴"
        },
        
        # 自动化测试
        {
            "title": "什么是自动化测试？什么时候适合做自动化测试？",
            "answer": """自动化测试是使用脚本或工具代替人工执行测试用例的过程，可以提高测试效率，减少重复劳动。

适合做自动化测试的场景：
1. 需求稳定，不会频繁变更
2. 项目周期长，需要频繁回归测试
3. 重复度高的测试场景（如冒烟测试、回归测试）
4. 性能测试、压力测试等人工无法实现的测试
5. 多平台、多环境的兼容性测试

不适合的场景：
1. 需求频繁变更的项目
2. 项目周期短，一次性的项目
3. 涉及视觉、用户体验等需要人工判断的测试
4. 没有明确预期结果的测试

自动化测试 ROI = 自动化收益 / 自动化成本，当ROI大于1时才值得做自动化。""",
            "category": "自动化测试",
            "difficulty": "medium",
            "position_level": "中级",
            "tags": "自动化测试,测试策略",
            "company": "腾讯"
        },
        {
            "title": "Selenium的工作原理是什么？隐式等待和显式等待的区别？",
            "answer": """Selenium工作原理：
1. Selenium Client库（Java/Python等）发送测试命令给浏览器驱动
2. 浏览器驱动解析命令，转化为浏览器能理解的指令
3. 浏览器执行指令，将结果返回给驱动
4. 驱动将结果返回给测试脚本

隐式等待：
- 设置一个全局的等待时间，在查找元素时如果元素不存在，会等待指定时间再抛出异常
- 对所有查找元素的操作都生效
- 缺点是不够灵活，可能会导致测试时间变长

显式等待：
- 针对特定的元素设置等待条件，直到条件满足才继续执行
- 可以设置超时时间和轮询间隔
- 更加灵活，可以针对不同元素设置不同的等待条件
- 推荐优先使用显式等待

最佳实践：优先使用显式等待，尽量避免使用线程休眠，隐式等待设置合理的超时时间。""",
            "category": "自动化测试",
            "difficulty": "hard",
            "position_level": "中级",
            "tags": "Selenium,UI自动化,等待机制",
            "company": "百度"
        },
        
        # 接口测试
        {
            "title": "什么是接口测试？接口测试的优势是什么？",
            "answer": """接口测试是测试系统组件间接口的一种测试，主要验证接口的功能正确性、性能、稳定性和安全性。

接口测试的优势：
1. 测试可以更早介入，在UI开发完成前就可以进行测试
2. 发现问题的成本更低，更早发现缺陷修复成本越低
3. 测试执行速度更快，比UI自动化执行效率高很多
4. 测试覆盖率更高，可以覆盖一些UI层面无法覆盖的场景
5. 稳定性更好，不容易受UI变更的影响
6. 更适合自动化，维护成本更低

接口测试通常是测试金字塔的中间层，是质量保障的重要环节。""",
            "category": "接口测试",
            "difficulty": "medium",
            "position_level": "中级",
            "tags": "接口测试,测试分层",
            "company": "美团"
        },
        {
            "title": "HTTP请求的GET和POST方法有什么区别？",
            "answer": """GET和POST是HTTP协议中最常用的两种请求方法，主要区别：
1. 功能：GET用于获取资源，POST用于提交数据
2. 参数位置：GET参数放在URL中，POST参数放在请求体中
3. 参数长度限制：GET受URL长度限制（一般2KB左右），POST没有限制
4. 安全性：POST比GET相对安全，因为参数不在URL中显示
5. 缓存：GET请求可以被缓存，POST请求默认不能被缓存
6. 幂等性：GET是幂等的，多次请求结果相同；POST是非幂等的，多次请求可能产生不同结果
7. 编码方式：GET只能进行URL编码，POST支持多种编码方式

在实际使用中，应该根据业务场景选择合适的请求方法。""",
            "category": "接口测试",
            "difficulty": "easy",
            "position_level": "初级",
            "tags": "HTTP,接口基础",
            "company": "通用"
        },
        
        # 编程题
        {
            "title": "写一个Python函数，实现冒泡排序算法。",
            "answer": """```python
def bubble_sort(arr):
    n = len(arr)
    # 遍历所有数组元素
    for i in range(n):
        # 最后i个元素已经有序
        for j in range(0, n-i-1):
            # 遍历数组从0到n-i-1
            # 如果当前元素大于下一个元素，交换
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# 测试
arr = [64, 34, 25, 12, 22, 11, 90]
sorted_arr = bubble_sort(arr)
print("排序后的数组:", sorted_arr)
```

冒泡排序的时间复杂度是O(n²)，空间复杂度是O(1)，是一种稳定的排序算法。适用于小规模数据排序。

优化点：可以添加一个标志位，如果某一轮没有发生交换，说明数组已经有序，可以提前退出。""",
            "category": "编程",
            "difficulty": "medium",
            "position_level": "中级",
            "tags": "Python,算法,排序",
            "company": "拼多多"
        },
        
        # HR面
        {
            "title": "请介绍一下你自己？",
            "answer": """回答要点：
1. 简短的个人背景介绍，专业、工作年限
2. 核心技能和擅长的领域，和应聘岗位的匹配点
3. 过往的重要项目经验和取得的成果
4. 个人的职业规划和为什么应聘这个岗位

回答示例：
您好，我有3年软件测试工作经验，主要擅长功能测试、接口测试和自动化测试。之前在XX公司负责XX项目的测试工作，搭建了接口自动化测试框架，把回归测试时间从3天缩短到了4小时，缺陷发现率提升了30%。我对测试技术很感兴趣，平时也会学习一些新的测试工具和方法。我了解到贵公司在XX领域很有影响力，而且这个岗位很符合我的职业发展方向，所以我来应聘这个岗位。

回答要简洁，突出优势，和岗位匹配，避免冗长。""",
            "category": "HR面",
            "difficulty": "medium",
            "position_level": "通用",
            "tags": "HR面试,自我介绍",
            "company": "通用"
        },
        {
            "title": "你的缺点是什么？",
            "answer": """回答要点：
1. 不要说自己没有缺点，也不要说对岗位有致命影响的缺点
2. 说一些真实存在但不影响核心工作的缺点
3. 重点说你正在如何改进这个缺点
4. 缺点要具体，不要太笼统

回答示例：
我觉得我之前的缺点是有时候过于追求完美，会在一些细节上花太多时间，导致有时候项目进度会有一点延迟。后来我意识到这个问题，现在我会先分清楚优先级，先保证核心功能的质量，再去优化细节，而且会提前规划好时间，现在已经改善很多了。

避免回答：我最大的缺点就是太追求完美了（太假），或者我对测试技术掌握还不够（直接凉）。""",
            "category": "HR面",
            "difficulty": "hard",
            "position_level": "通用",
            "tags": "HR面试,常见问题",
            "company": "通用"
        }
    ]
    
    for q in interview_questions:
        iq = InterviewQuestion(**q)
        db.session.add(iq)
    
    db.session.commit()
    print(f"Created {len(interview_questions)} interview questions!")

    print("\nAll data initialized successfully!")
    print("\nSummary:")
    print(f"- 阶段1（测试入门）：{len(stage1_paths)}个学习路径")
    print(f"- 阶段2（功能测试）：{len(stage2_paths)}个学习路径")
    print(f"- 阶段3（技术进阶）：{len(stage3_paths)}个学习路径")
    print(f"- 阶段4（自动化测试）：{len(stage4_paths)}个学习路径")
    print(f"- 阶段5（测试架构师）：{len(stage5_paths)}个学习路径")
    print(f"- 总计：{len(all_paths)}个学习路径，{len(stage1_exercises) + len(code_exercises)}个习题，{len(interview_questions)}道面试题")
    print("\nAdmin账号：admin / admin123")
