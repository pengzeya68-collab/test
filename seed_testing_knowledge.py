"""
测试知识体系填充脚本
使用方法: python seed_testing_knowledge.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 学习路径数据
LEARNING_PATHS = [
    {
        "title": "软件测试基础",
        "description": "从零开始学习软件测试的核心概念和方法，建立扎实的测试理论基础。",
        "learning_objectives": "掌握软件测试的基本概念，理解测试生命周期、掌握测试用例设计方法、学会提交和管理缺陷报告",
        "knowledge_outline": "测试的定义与目的|软件质量模型|测试生命周期|测试用例设计方法|缺陷管理与报告",
        "supporting_resources": "ISTQB基础级大纲",
        "prerequisites": "",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 20,
    },
    {
        "title": "计算机基础知识",
        "description": "学习软件测试工程师必备的计算机基础知识，包括操作系统、网络和数据库。",
        "learning_objectives": "理解操作系统基本原理、掌握HTTP/HTTPS协议、理解SQL基础查询",
        "knowledge_outline": "操作系统概念|计算机网络基础|HTTP协议详解|数据库基础与SQL",
        "supporting_resources": "计算机网络教材、SQL基础教程",
        "prerequisites": "",
        "difficulty": "beginner",
        "stage": 1,
        "estimated_hours": 30,
    },
    {
        "title": "功能测试实践",
        "description": "学习Web和API的功能测试方法，掌握主流测试工具的使用。",
        "learning_objectives": "掌握Web测试方法、熟练使用Postman进行API测试、理解前后端交互原理",
        "knowledge_outline": "Web测试方法|表单测试|Cookie和Session测试|API测试|Postman使用",
        "supporting_resources": "Postman官方文档、RESTful API设计规范",
        "prerequisites": "计算机基础知识",
        "difficulty": "intermediate",
        "stage": 2,
        "estimated_hours": 25,
    },
    {
        "title": "测试用例设计方法",
        "description": "深入学习各种测试用例设计方法，提高测试覆盖率和效率。",
        "learning_objectives": "掌握等价类划分、边界值分析、判定表法、状态迁移法、正交试验法",
        "knowledge_outline": "等价类划分法|边界值分析法|判定表法|状态迁移法|因果图法|正交试验法",
        "supporting_resources": "ISTQB大纲、测试用例设计经典案例",
        "prerequisites": "软件测试基础",
        "difficulty": "intermediate",
        "stage": 2,
        "estimated_hours": 20,
    },
    {
        "title": "Python编程基础",
        "description": "学习Python编程，为自动化测试打下坚实基础。",
        "learning_objectives": "掌握Python基础语法，理解面向对象编程，能编写简单的Python脚本",
        "knowledge_outline": "Python基础语法|数据类型与运算符|控制流程|函数与模块|面向对象编程|文件操作",
        "supporting_resources": "Python官方教程",
        "prerequisites": "",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 40,
    },
    {
        "title": "Selenium Web自动化测试",
        "description": "学习使用Selenium进行Web UI自动化测试。",
        "learning_objectives": "掌握Selenium定位元素方法，理解等待机制，能编写完整的Web自动化测试脚本",
        "knowledge_outline": "Selenium架构|元素定位方法|等待机制|浏览器操作|页面对象模型",
        "supporting_resources": "Selenium官方文档",
        "prerequisites": "Python编程基础",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 30,
    },
    {
        "title": "Pytest测试框架",
        "description": "学习使用Pytest框架编写专业的Python自动化测试。",
        "learning_objectives": "掌握Pytest fixture、参数化、断言、报告生成，能搭建完整的自动化测试框架",
        "knowledge_outline": "Pytest安装配置|fixture机制|参数化测试|断言与报告|数据驱动|框架封装",
        "supporting_resources": "Pytest官方文档",
        "prerequisites": "Python编程基础",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 25,
    },
    {
        "title": "接口自动化测试",
        "description": "学习基于Python的接口自动化测试。",
        "learning_objectives": "掌握Requests库使用、接口签名认证、数据驱动、接口自动化框架搭建",
        "knowledge_outline": "HTTP协议深入|Requests库|接口签名认证|数据驱动|接口Mock|框架封装",
        "supporting_resources": "Requests官方文档",
        "prerequisites": "Python编程基础 + 功能测试实践",
        "difficulty": "intermediate",
        "stage": 3,
        "estimated_hours": 30,
    },
    {
        "title": "性能测试",
        "description": "学习使用Locust和JMeter进行性能测试。",
        "learning_objectives": "理解性能测试指标、掌握Locust脚本编写、能进行负载测试和结果分析",
        "knowledge_outline": "性能测试基础|响应时间/吞吐量/TPS|Locust脚本|JMeter使用|结果分析",
        "supporting_resources": "Locust官方文档",
        "prerequisites": "Python编程基础 + 接口测试",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 35,
    },
    {
        "title": "安全测试基础",
        "description": "学习常见Web安全漏洞及测试方法。",
        "learning_objectives": "理解OWASP Top 10、掌握SQL注入/XSS/CSRF测试方法、了解安全测试工具",
        "knowledge_outline": "安全测试概述|SQL注入|XSS跨站脚本|CSRF|文件上传漏洞|认证与授权",
        "supporting_resources": "OWASP官方文档",
        "prerequisites": "Web测试 + Python基础",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 30,
    },
    {
        "title": "CI/CD持续集成",
        "description": "学习将自动化测试集成到CI/CD流水线中。",
        "learning_objectives": "理解DevOps理念、掌握GitHub Actions/Jenkins使用、能搭建完整的自动化测试流水线",
        "knowledge_outline": "DevOps基础|Git与GitHub|GitHub Actions|Jenkins|Docker基础|自动化测试集成",
        "supporting_resources": "Git官方文档、GitHub Actions文档",
        "prerequisites": "自动化测试基础",
        "difficulty": "advanced",
        "stage": 4,
        "estimated_hours": 30,
    },
]

# 面试题目数据
INTERVIEW_QUESTIONS = [
    {
        "title": "什么是软件测试？为什么需要软件测试？",
        "category": "测试理论",
        "difficulty": "easy",
        "position_level": "初级测试工程师",
        "description": "请解释软件测试的定义、目的和重要性。",
        "answer": """软件测试的定义：
软件测试是通过执行软件来发现其中的缺陷（Bug/Defect），验证软件是否满足预期需求的活动。

为什么需要软件测试：
1. 发现缺陷：通过测试发现软件中的错误和缺陷
2. 验证质量：验证软件满足用户需求和规格说明
3. 降低风险：减少软件上线后出现问题的风险
4. 提升信心：让开发团队和用户对软件质量有信心
5. 成本效益：缺陷发现越早，修复成本越低

软件测试的重要性：
- 提高软件质量
- 保障用户体验
- 保护公司声誉
- 避免重大损失
- 满足合规要求（如金融、医疗等行业）""",
        "tags": '["测试基础", "软件质量", "测试目的"]',
    },
    {
        "title": "软件测试与软件调试有什么区别？",
        "category": "测试理论",
        "difficulty": "easy",
        "position_level": "初级测试工程师",
        "description": "比较软件测试和软件调试的目的、方法、参与人员等。",
        "answer": """软件测试 vs 软件调试：

目的不同：
- 测试：发现软件中的缺陷，验证软件是否满足需求
- 调试：定位并修复已发现的缺陷

参与人员不同：
- 测试：主要由测试工程师执行
- 调试：由开发人员执行

方法不同：
- 测试：从已知条件出发，通过执行被测程序来发现缺陷
- 调试：从观察到的异常现象出发，通过分析来找出原因

阶段不同：
- 测试：通常在开发完成后进行
- 调试：在开发过程中发现问题时进行

目标不同：
- 测试：证明软件存在缺陷
- 调试：证明软件不存在缺陷（消除已知的缺陷）""",
        "tags": '["测试基础", "调试"]',
    },
    {
        "title": "请描述软件测试的生命周期",
        "category": "测试理论",
        "difficulty": "medium",
        "position_level": "初级测试工程师",
        "description": "详细描述测试生命周期的各个阶段。",
        "answer": """软件测试生命周期（STLC）包含以下阶段：

1. 需求分析（Requirement Analysis）
   - 分析测试需求
   - 确定测试范围
   - 识别可测试性

2. 测试计划（Test Planning）
   - 制定测试策略
   - 估算测试资源和时间
   - 编写测试计划

3. 测试设计（Test Design）
   - 编写测试用例
   - 评审测试用例
   - 准备测试数据

4. 测试环境搭建（Test Environment Setup）
   - 准备测试环境
   - 搭建自动化测试框架
   - 准备测试工具

5. 测试执行（Test Execution）
   - 执行测试用例
   - 记录测试结果
   - 提交缺陷报告

6. 测试收尾（Test Closure）
   - 分析测试结果
   - 编写测试报告
   - 总结经验教训
   - 归档测试文档""",
        "tags": '["测试生命周期", "STLC", "测试阶段"]',
    },
    {
        "title": "什么是测试用例？设计测试用例的方法有哪些？",
        "category": "测试用例设计",
        "difficulty": "medium",
        "position_level": "初级测试工程师",
        "description": "解释测试用例的概念和常用的测试用例设计方法。",
        "answer": """测试用例（Test Case）是为某个特定测试目标而编写的输入数据、执行条件和预期结果的集合。

常用的测试用例设计方法：

1. 等价类划分法（Equivalence Partitioning）
   - 将输入数据分成若干等价类
   - 从每个等价类中选取少量代表性数据进行测试
   - 分为有效等价类和无效等价类

2. 边界值分析法（Boundary Value Analysis）
   - 针对输入/输出的边界值进行测试
   - 通常选取边界值及其附近的数据

3. 判定表法（Decision Table Testing）
   - 适用于多个输入条件相互组合的情况
   - 列出所有条件组合和对应的结果

4. 状态迁移法（State Transition Testing）
   - 适用于测试对象的状态转换
   - 测试状态之间的转换是否正确

5. 因果图法（Cause-Effect Graph）
   - 分析输入条件之间的关系
   - 生成判定表

6. 正交试验法（Orthogonal Array Testing）
   - 使用正交表来减少测试用例数量
   - 保证测试覆盖的均匀性

7. 场景法（Scenario Testing）
   - 基于业务流程设计测试场景
   - 从用户角度模拟实际使用场景""",
        "tags": '["测试用例", "等价类", "边界值", "判定表"]',
    },
    {
        "title": "什么是Alpha测试和Beta测试？有什么区别？",
        "category": "测试理论",
        "difficulty": "medium",
        "position_level": "初级测试工程师",
        "description": "解释Alpha测试和Beta测试的概念和区别。",
        "answer": """Alpha测试（Alpha Testing）：
- 定义：在开发环境进行，由内部测试人员在开发人员指导下进行测试
- 地点：开发公司内部
- 测试人员：内部测试工程师 + 开发人员指导
- 发现缺陷后的修复：可以立即反馈给开发人员修复
- 优点：缺陷发现后可快速修复
- 缺点：测试范围有限，可能遗漏用户角度的问题

Beta测试（Beta Testing）：
- 定义：在真实用户环境进行，由真实用户进行测试
- 地点：用户实际使用环境
- 测试人员：真实用户（通过邀请的外部用户）
- 发现缺陷后的修复：通过反馈收集，由开发团队统一修复
- 优点：能够发现真实用户环境下的实际问题
- 缺点：修复周期较长

主要区别：
1. 测试环境不同：Alpha在开发环境，Beta在用户环境
2. 测试人员不同：Alpha是内部人员，Beta是真实用户
3. 发现问题的修复方式不同：Alpha可立即修复，Beta统一收集后修复
4. 测试的深入程度不同：Alpha更系统全面，Beta更贴近实际使用""",
        "tags": '["Alpha测试", "Beta测试", "验收测试"]',
    },
    {
        "title": "什么是冒烟测试、回归测试、功能测试？",
        "category": "测试理论",
        "difficulty": "easy",
        "position_level": "初级测试工程师",
        "description": "解释几种常见测试类型的概念和应用场景。",
        "answer": """1. 冒烟测试（Smoke Testing）
   - 概念：对软件的基本功能进行快速验证，确保核心功能可以运行
   - 目的：决定是否进行进一步的详细测试
   - 特点：测试用例少，执行速度快，覆盖核心功能
   - 应用：每次构建后快速验证

2. 功能测试（Functional Testing）
   - 概念：验证软件的功能是否符合需求规格说明书
   - 目的：确保所有功能按需求正常工作
   - 方法：黑盒测试，基于需求文档
   - 覆盖：所有功能点、用户操作

3. 回归测试（Regression Testing）
   - 概念：在软件修改后，重新执行之前的测试用例，确保修改没有引入新问题
   - 目的：保证修改没有破坏现有功能
   - 特点：需要频繁重复执行
   - 方法：通常结合自动化测试提高效率

4. 集成测试（Integration Testing）
   - 概念：将各个模块组合起来进行测试
   - 目的：发现模块之间的接口问题
   - 方法：自顶向下或自底向上

5. 系统测试（System Testing）
   - 概念：对整个系统进行测试
   - 目的：验证系统整体满足需求""",
        "tags": '["冒烟测试", "回归测试", "功能测试", "测试类型"]',
    },
    {
        "title": "请解释HTTP协议的工作原理",
        "category": "计算机基础",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "详细解释HTTP协议的工作原理，包括请求响应模型、状态码等。",
        "answer": """HTTP（HyperText Transfer Protocol）超文本传输协议：

工作原理 - 请求/响应模型：
1. 客户端（浏览器）向服务器发送HTTP请求
2. 服务器接收请求，处理后返回HTTP响应
3. 客户端接收响应并展示结果

HTTP请求组成：
- 请求行：方法 + URL + 协议版本
- 请求头：键值对，包含客户端信息
- 空行
- 请求体：POST/PUT请求的数据

常见HTTP方法：
- GET：获取资源
- POST：提交数据
- PUT：更新资源
- DELETE：删除资源
- PATCH：部分更新

HTTP响应组成：
- 状态行：协议版本 + 状态码 + 状态消息
- 响应头：服务器信息
- 空行
- 响应体：返回的数据

常见状态码：
- 1xx：信息性响应
- 2xx：成功（200 OK, 201 Created）
- 3xx：重定向（301 Moved, 302 Found）
- 4xx：客户端错误（400 Bad Request, 401 Unauthorized, 404 Not Found）
- 5xx：服务器错误（500 Internal Server Error, 502 Bad Gateway）

HTTP特点：
- 无状态：每个请求都是独立的
- 无连接：基于TCP，一次请求响应后断开
- 可扩展：可添加自定义头信息""",
        "tags": '["HTTP协议", "网络基础", "请求响应"]',
    },
    {
        "title": "GET请求和POST请求有什么区别？",
        "category": "计算机基础",
        "difficulty": "easy",
        "position_level": "初级测试工程师",
        "description": "比较GET和POST两种HTTP方法的区别。",
        "answer": """GET vs POST 对比：

1. 参数位置：
   - GET：参数放在URL中，?后跟查询字符串
   - POST：参数放在请求体中，不会在URL显示

2. 安全性：
   - GET：参数暴露在URL，不适合传输敏感信息
   - POST：参数在请求体中，相对更安全

3. 数据大小限制：
   - GET：受URL长度限制（浏览器通常2KB-8KB）
   - POST：理论上无大小限制，受服务器配置影响

4. 缓存：
   - GET：请求可被缓存
   - POST：请求通常不会被缓存

5. 幂等性：
   - GET：幂等，多次请求结果相同
   - POST：非幂等，每次请求可能产生不同结果

6. 使用场景：
   - GET：查询数据、获取资源（如搜索）
   - POST：提交表单、上传文件、登录注册

7. 书签收藏：
   - GET：URL可被收藏为书签
   - POST：参数不在URL，无法收藏""",
        "tags": '["GET", "POST", "HTTP方法"]',
    },
    {
        "title": "请解释Cookie和Session的区别",
        "category": "计算机基础",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "详细解释Cookie和Session的概念和区别。",
        "answer": """Cookie：
- 概念：服务器发送到用户浏览器并保存在本地的数据
- 存储位置：用户本地浏览器
- 存储格式：键值对
- 大小限制：单个Cookie不超过4KB
- 生命周期：可设置过期时间
- 安全性：可被用户禁用或清除

Session：
- 概念：服务器端存储的用户会话信息
- 存储位置：服务器内存/数据库
- 存储格式：对象
- 大小限制：取决于服务器配置
- 生命周期：会话结束（浏览器关闭或超时）

工作原理：
1. 用户首次访问，服务器创建Session，生成SessionID
2. 服务器将SessionID通过Cookie发送给客户端
3. 后续请求，浏览器自动携带Cookie中的SessionID
4. 服务器根据SessionID找到对应的会话数据

主要区别：
1. 存储位置：Cookie在客户端，Session在服务器
2. 安全性：Session更安全（数据在服务器）
3. 资源消耗：Session占用服务器资源，Cookie不占用
4. 数据类型：Cookie只支持字符串，Session支持任意类型
5. 大小限制：Cookie有大小限制，Session理论上无限制

测试关注点：
- Cookie：禁用后功能是否正常、数据是否加密
- Session：超时验证、共享登录（多设备）""",
        "tags": '["Cookie", "Session", "认证"]',
    },
    {
        "title": "如何描述一个高质量的缺陷报告？",
        "category": "缺陷管理",
        "difficulty": "medium",
        "position_level": "初级测试工程师",
        "description": "描述缺陷报告应包含的核心要素和描述方法。",
        "answer": """高质量缺陷报告的核心要素：

1. 缺陷标题
   - 简洁明了，一眼看出问题
   - 包含模块名和问题描述
   - 示例：登录页面-输入正确密码后点击登录无响应

2. 缺陷描述
   - 详细描述问题现象
   - 描述预期行为和实际行为
   - 描述复现步骤

3. 复现步骤
   - 清晰的步骤编号
   - 每步具体操作
   - 包含测试数据
   - 可任何人按步骤复现

4. 预期结果
   - 描述应有的正确行为

5. 实际结果
   - 描述当前实际发生的错误行为

6. 环境信息
   - 操作系统
   - 浏览器版本
   - APP版本
   - 网络环境

7. 缺陷级别
   - Blocker：系统无法使用
   - Critical：核心功能无法使用
   - Major：主要功能受影响
   - Minor：次要功能问题
   - Trivial：界面瑕疵

8. 附件
   - 截图
   - 日志
   - 视频录屏

高质量缺陷报告标准：
- 他人可复现
- 不冗余不遗漏
- 客观描述事实
- 问题明确、修复建议合理""",
        "tags": '["缺陷报告", "Bug描述", "缺陷管理"]',
    },
    {
        "title": "缺陷的生命周期是怎样的？",
        "category": "缺陷管理",
        "difficulty": "medium",
        "position_level": "初级测试工程师",
        "description": "描述缺陷从发现到关闭的完整生命周期。",
        "answer": """缺陷生命周期（Bug Life Cycle）：

1. New（新建）
   - 测试人员发现缺陷，提交缺陷报告
   - 状态为新建，等待确认

2. Open（打开）
   - 开发人员确认是有效缺陷
   - 开始着手修复

3. In Progress（进行中）
   - 开发人员正在修复缺陷

4. Fixed（已修复）
   - 开发人员完成修复
   - 等待测试人员验证

5. Pending Re-test（待验证）
   - 等待测试人员进行回归测试

6. Verified（已验证）
   - 测试人员确认修复有效
   - 缺陷已解决

7. Closed（关闭）
   - 缺陷彻底关闭

可能的状态转换：
- New -> Rejected（缺陷被拒绝）
- New -> Duplicate（重复缺陷）
- New -> Deferred（推迟处理）
- Reopened（重新打开）
- 修复后验证失败 -> 重新进入开发流程

测试人员在缺陷生命周期中的职责：
- 准确描述和提交缺陷
- 跟踪缺陷状态
- 验证修复结果
- 确保缺陷被正确处理""",
        "tags": '["缺陷生命周期", "Bug状态", "缺陷流程"]',
    },
    {
        "title": "Python中的列表和元组有什么区别？",
        "category": "Python编程",
        "difficulty": "easy",
        "position_level": "初级测试工程师",
        "description": "比较Python列表和元组的特性和使用场景。",
        "answer": """列表（List）vs 元组（Tuple）：

1. 可变性：
   - 列表：可变，可以修改、添加、删除元素
   - 元组：不可变，一旦创建不能修改

2. 语法：
   - 列表：[1, 2, 3]
   - 元组：(1, 2, 3) 或 1, 2, 3

3. 性能：
   - 列表：需要更多内存，支持更多操作
   - 元组：更轻量，性能略好（不可变对象Python会缓存）

4. 功能：
   - 列表：append(), remove(), insert()等方法
   - 元组：只有count(), index()两个方法

5. 使用场景：
   - 列表：需要动态修改的数据，如用户列表、购物车
   - 元组：配置信息、函数返回值、字典的键

6. 哈希：
   - 列表：不可哈希，不能作为字典键
   - 元组：可哈希（如果元素都是可哈希的），可作为字典键

测试关注点：
- 检查API返回的数据类型
- 验证数据结构的可变性
- 确保测试数据稳定性""",
        "tags": '["Python", "列表", "元组", "数据结构"]',
    },
    {
        "title": "Selenium中有哪些元素定位方式？如何选择？",
        "category": "Web测试",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "介绍Selenium的各种定位方式及适用场景。",
        "answer": """Selenium元素定位方式：

1. ID定位：driver.find_element(By.ID, "username")
   - 最推荐，速度最快
   - 适用于开发规范、ID唯一

2. Name定位：driver.find_element(By.NAME, "password")
   - 适用于表单元素
   - 不保证唯一性

3. Class Name定位：driver.find_element(By.CLASS_NAME, "form-input")
   - 适用于CSS类名唯一
   - 复合类名只能用其中一个

4. Tag Name定位：driver.find_element(By.TAG_NAME, "input")
   - 较少使用，通常定位多个

5. Link Text定位：driver.find_element(By.LINK_TEXT, "登录")
   - 适用于超链接文本

6. Partial Link Text：driver.find_element(By.PARTIAL_LINK_TEXT, "登录")
   - 文本部分匹配

7. XPath定位：driver.find_element(By.XPATH, "//div[@class='form']/input")
   - 最灵活，功能强大
   - 支持路径、属性、文本定位
   - 缺点：路径复杂时性能较差

8. CSS Selector定位：driver.find_element(By.CSS_SELECTOR, "div.form > input")
   - 语法简洁
   - 性能比XPath好
   - 推荐使用

选择建议：
- 优先使用ID（最快最稳定）
- 其次CSS Selector（简洁高效）
- XPath用于复杂场景（最灵活但较慢）
- 避免使用索引定位（不稳定）

最佳实践：
- 与开发约定ID规范
- 优先使用data-testid属性
- 避免使用绝对路径
- 使用相对路径定位""",
        "tags": '["Selenium", "元素定位", "Web自动化"]',
    },
    {
        "title": "Selenium中显式等待和隐式等待有什么区别？",
        "category": "Web测试",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "解释两种等待方式的区别和使用场景。",
        "answer": """显式等待 vs 隐式等待：

隐式等待（Implicit Wait）：
- 设置一次，全局生效
- 针对所有元素查找操作
- 超时后抛出NoSuchElementException
- 示例：driver.implicitly_wait(10)

显式等待（Explicit Wait）：
- 针对单个元素设置
- 轮询检查条件是否满足
- 超时后抛出TimeoutException
- 更灵活，可等待不同条件

常用等待条件：
- presence_of_element_located：元素存在
- visibility_of_element_located：元素可见
- element_to_be_clickable：元素可点击
- text_to_be_present_in_element：元素包含文本

对比：
- 作用域：隐式等待全局，显式等待单个元素
- 灵活性：隐式等待低，显式等待高
- 资源消耗：隐式等待较低，显式等待较高

最佳实践：
- 避免混用两种等待
- 推荐显式等待，灵活精确
- 设置合理的超时时间
- 优先使用自定义等待条件""",
        "tags": '["Selenium", "显式等待", "隐式等待", "Web自动化"]',
    },
    {
        "title": "RESTful API的设计原则是什么？",
        "category": "API测试",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "解释RESTful API的设计规范和最佳实践。",
        "answer": """RESTful API 设计原则：

1. 资源导向（Resource-based）
   - 使用名词表示资源：/users, /orders
   - 不是动词：/getUsers（错误）

2. HTTP方法对应操作
   - GET：查询资源
   - POST：创建资源
   - PUT：完整更新资源
   - PATCH：部分更新资源
   - DELETE：删除资源

3. 使用HTTP状态码
   - 200：成功
   - 201：创建成功
   - 400：请求参数错误
   - 401：未认证
   - 403：权限不足
   - 404：资源不存在
   - 500：服务器错误

4. 无状态（Stateless）
   - 每个请求包含所有必要信息
   - 服务器不保存客户端状态

5. 路径规范
   - 使用小写字母
   - 用横杠分隔：/user-profiles
   - 嵌套资源：/users/123/orders

API测试关注点：
- 验证HTTP方法使用正确
- 检查状态码是否规范
- 验证请求头和响应头
- 检查分页和过滤参数
- 验证错误响应格式""",
        "tags": '["RESTful", "API设计", "REST API"]',
    },
    {
        "title": "Pytest中的fixture是什么？如何使用？",
        "category": "自动化测试",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "详细解释Pytest fixture的概念和使用方法。",
        "answer": """Pytest Fixture：

概念：Fixture是用于为测试提供数据、设置前置条件、清理环境的函数。

基本使用：
    @pytest.fixture
    def login_user():
        return {"username": "test", "password": "123456"}

Scope（作用域）：
- function：每个函数执行一次（默认）
- class：每个类执行一次
- module：每个模块执行一次
- session：整个测试会话执行一次

带参数的Fixture：
    @pytest.fixture(params=["chrome", "firefox"])
    def browser(request):
        return request.param

autouse自动执行：
    @pytest.fixture(autouse=True)
    def setup_teardown():
        print("Setup")
        yield
        print("Teardown")

conftest.py：
- 共享fixture的配置文件
- 放在tests目录下自动加载

常见fixture应用场景：
- 数据库连接
- API客户端
- 测试数据准备
- 浏览器实例
- 登录状态""",
        "tags": '["Pytest", "Fixture", "自动化测试"]',
    },
    {
        "title": "性能测试的关键指标有哪些？",
        "category": "性能测试",
        "difficulty": "medium",
        "position_level": "中级测试工程师",
        "description": "介绍性能测试中需要关注的核心指标。",
        "answer": """性能测试关键指标：

1. 响应时间（Response Time）
   - 定义：请求发出到收到响应的时间
   - 组成：网络延迟 + 服务器处理时间 + 页面渲染时间
   - 行业标准：3秒内用户可接受，5秒内勉强接受

2. 吞吐量（Throughput）
   - 定义：单位时间内处理的请求数量
   - 单位：TPS（每秒事务数）、QPS（每秒查询数）
   - 反映系统处理能力

3. 并发数（Concurrency）
   - 定义：同时发起请求的用户数
   - 区分：虚拟用户数 vs 真实并发数

4. 资源利用率
   - CPU使用率
   - 内存使用率
   - 磁盘I/O
   - 网络带宽

5. 错误率
   - 定义：失败请求 / 总请求数
   - 关注：5xx错误率、接口超时率

性能测试类型：
- 基准测试：单用户性能
- 负载测试：正常压力下性能
- 压力测试：超过正常负载
- 容量测试：最大承载能力
- 稳定性测试：长时间运行""",
        "tags": '["性能测试", "TPS", "响应时间", "并发"]',
    },
    {
        "title": "什么是SQL注入？如何测试？",
        "category": "安全测试",
        "difficulty": "medium",
        "position_level": "高级测试工程师",
        "description": "解释SQL注入原理及测试方法。",
        "answer": """SQL注入（SQL Injection）：

原理：
攻击者通过在用户输入中插入恶意SQL语句，来操作数据库。

示例：
正常查询：SELECT * FROM users WHERE username='admin' AND password='123456'
注入攻击：username: admin' OR '1'='1
实际执行：SELECT * FROM users WHERE username='admin' OR '1'='1' AND password='anything'

常见注入点：
- 用户登录表单
- 搜索框
- URL参数
- HTTP头

SQL注入测试用例：
1. ' OR '1'='1
2. ' OR 1=1--
3. admin'--
4. ' UNION SELECT * FROM users--

防护措施验证：
- 参数化查询（Prepared Statements）
- 输入验证
- 存储过程
- ORM框架

安全测试要点：
- 测试所有用户输入点
- 使用自动化工具辅助（SQLMAP）
- 验证防护措施有效性
- 检查错误信息是否泄露敏感信息""",
        "tags": '["SQL注入", "安全测试", "渗透测试"]',
    },
    {
        "title": "什么是XSS跨站脚本攻击？如何防护和测试？",
        "category": "安全测试",
        "difficulty": "medium",
        "position_level": "高级测试工程师",
        "description": "解释XSS攻击类型、防护方法和测试要点。",
        "answer": """XSS（Cross-Site Scripting）跨站脚本攻击：

原理：
攻击者在网页中注入恶意JavaScript代码，当其他用户访问时执行。

三种XSS类型：

1. 反射型XSS
   - 恶意脚本作为用户输入立即返回
   - 示例：搜索功能返回搜索关键词时未转义

2. 存储型XSS
   - 恶意脚本存储在数据库中
   - 每次页面加载时执行
   - 最危险，如评论区发表恶意脚本

3. DOM型XSS
   - 前端JavaScript处理URL参数时执行
   - 不经过服务器

XSS测试用例：
1. <script>alert('XSS')</script>
2. <img src=x onerror=alert('XSS')>
3. <svg onload=alert('XSS')>
4. javascript:alert('XSS')

防护措施：
- 输入验证：过滤特殊字符
- 输出编码：HTML转义
- HttpOnly Cookie：防止JavaScript读取Cookie
- Content Security Policy (CSP)

XSS测试要点：
- 测试所有输入点
- 测试输出显示点
- 验证编码转义
- 检查CSP策略配置""",
        "tags": '["XSS", "跨站脚本", "安全测试"]',
    },
    {
        "title": "Linux常用命令有哪些？",
        "category": "Linux",
        "difficulty": "easy",
        "position_level": "初级测试工程师",
        "description": "列出测试工程师常用的Linux命令。",
        "answer": """测试工程师常用Linux命令：

文件操作：
- ls -la：列出所有文件（包括隐藏）
- cd /path：切换目录
- pwd：显示当前目录
- mkdir dirname：创建目录
- rm -rf dirname：删除目录
- cp file1 file2：复制文件
- mv file1 file2：移动/重命名
- cat file：查看文件内容
- grep "pattern" file：搜索内容

进程管理：
- ps aux：查看所有进程
- ps aux | grep python：查找Python进程
- kill -9 PID：强制终止进程
- top：查看系统资源

网络命令：
- curl http://api.test.com：发送HTTP请求
- wget url：下载文件
- ping host：测试连通性
- netstat -tuln：查看监听端口

日志查看：
- tail -f app.log：实时跟踪日志
- grep -i error app.log：搜索错误

测试应用：
- tail -f /var/log/app.log | grep ERROR
- ps aux | grep uvicorn
- netstat -tuln | grep 5001
- curl -X POST http://localhost:5001/api/test""",
        "tags": '["Linux", "命令行", "服务器操作"]',
    },
    {
        "title": "如何设计一个可维护的自动化测试框架？",
        "category": "自动化测试",
        "difficulty": "hard",
        "position_level": "高级测试工程师",
        "description": "介绍自动化测试框架的设计模式和最佳实践。",
        "answer": """可维护自动化测试框架设计：

1. 分层架构
   - tests/：测试用例层
   - core/：核心层（基类、工具、配置）
   - pages/：页面对象层（Web）
   - services/：服务层
   - data/：数据层（测试数据、mock数据）

2. 页面对象模式（POM）
   - 每个页面一个类
   - 元素定位器集中管理
   - 页面操作封装成方法

3. 数据驱动
   - 测试数据与代码分离
   - 支持YAML/JSON/Excel
   - 参数化测试

4. 配置管理
   - 环境配置（dev/staging/prod）
   - 测试数据配置
   - 日志配置

5. 日志记录
   - 统一的日志格式
   - 分级记录（DEBUG/INFO/ERROR）
   - 测试执行过程可追溯

6. 报告集成
   - Pytest + Allure
   - HTML测试报告
   - 自动发送测试结果邮件

7. 持续集成
   - GitHub Actions
   - Jenkins Pipeline
   - 自动化触发测试执行

最佳实践：
- 保持测试用例简洁
- 避免硬编码
- 统一的命名规范
- 定期重构
- 代码审查""",
        "tags": '["自动化测试框架", "POM", "数据驱动", "架构设计"]',
    },
    {
        "title": "接口测试中如何处理签名认证？",
        "category": "API测试",
        "difficulty": "hard",
        "position_level": "高级测试工程师",
        "description": "解释常见的API签名认证原理及测试方法。",
        "answer": """常见API签名认证方式：

1. MD5/SHA签名
   - 将参数和密钥拼接后计算MD5/SHA值
   - 将签名附加到请求参数中

2. HMAC签名
   - 使用HMAC-SHA256等算法
   - 更安全的签名方式

3. OAuth 2.0
   - 授权码模式
   - 客户端凭证模式
   - 刷新令牌机制

4. JWT（JSON Web Token）
   - Header.Payload.Signature结构
   - 自包含令牌

签名认证测试方法：

1. 使用工具配置签名
   - Postman支持Pre-request Script生成签名

2. 编写Python脚本生成签名
   import hashlib
   import time

   def generate_sign(params, secret):
       timestamp = str(int(time.time()))
       sorted_params = sorted(params.items())
       params_str = "&".join([f"{k}={v}" for k, v in sorted_params])
       sign_str = f"{timestamp}{params_str}{secret}"
       sign = hashlib.md5(sign_str.encode()).hexdigest()
       return sign, timestamp

测试要点：
- 验证签名不正确时返回401
- 验证时间戳过期处理
- 验证签名算法正确性
- 验证密钥管理安全""",
        "tags": '["API测试", "签名认证", "安全测试"]',
    },
]


def seed_database():
    """填充数据库"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from fastapi_backend.models.models import LearningPath, InterviewQuestion, Base

    DATABASE_URL = "sqlite:///./instance/testmaster.db"
    engine = create_engine(DATABASE_URL, echo=False)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:

        print("开始填充学习路径...")

        for lp_data in LEARNING_PATHS:
            existing = session.query(LearningPath).filter_by(title=lp_data["title"]).first()
            if existing:
                print(f"  跳过已存在: {lp_data['title']}")
                continue

            lp = LearningPath(
                title=lp_data["title"],
                description=lp_data["description"],
                learning_objectives=lp_data["learning_objectives"],
                knowledge_outline=lp_data["knowledge_outline"],
                supporting_resources=lp_data["supporting_resources"],
                prerequisites=lp_data["prerequisites"],
                language="测试",
                difficulty=lp_data["difficulty"],
                stage=lp_data["stage"],
                estimated_hours=lp_data["estimated_hours"],
                is_public=True,
            )
            session.add(lp)
            print(f"  添加: {lp_data['title']}")

        session.commit()
        print(f"学习路径填充完成，共 {session.query(LearningPath).count()} 条")

        print("\n开始填充面试题目...")

        questions_added = 0
        for q_data in INTERVIEW_QUESTIONS:
            existing = session.query(InterviewQuestion).filter_by(title=q_data["title"]).first()
            if existing:
                print(f"  跳过已存在: {q_data['title'][:30]}...")
                continue

            question = InterviewQuestion(
                title=q_data["title"],
                category=q_data["category"],
                difficulty=q_data["difficulty"],
                position_level=q_data.get("position_level", "初级测试工程师"),
                description=q_data["description"],
                answer=q_data["answer"],
                tags=q_data.get("tags", "[]"),
                content=q_data.get("content", ""),
                prompt=q_data.get("prompt", ""),
                is_published=True,
            )
            session.add(question)
            questions_added += 1

        session.commit()
        print(f"面试题目填充完成，共 {session.query(InterviewQuestion).count()} 条，新增 {questions_added} 条")

        print("\n填充完成!")

    except Exception as e:
        session.rollback()
        print(f"错误: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("测试知识体系填充脚本")
    print("=" * 50)
    seed_database()
