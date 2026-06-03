"""
面试题库 V2 - 高质量面试题种子脚本

按学习路径分类，覆盖 5 个阶段 20 个学习路径的核心知识点。
题目类型：Q&A 文本题 + 编程代码题。
所有题目均有详细参考答案。
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import InterviewQuestion

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ============================================================
# Stage 1: 测试入门筑基
# ============================================================

TEST_BASICS = [
    {
        "title": "什么是软件测试？测试的目的是什么？",
        "category": "测试基础",
        "difficulty": "easy",
        "description": "请解释软件测试的定义和核心目的。",
        "answer": "软件测试是通过执行程序或系统来评估其是否满足规定需求，并发现缺陷的过程。\n\n核心目的：\n1. 发现缺陷：尽早发现软件中的错误和缺陷\n2. 验证需求：确认软件是否按照需求规格说明运行\n3. 预防缺陷：通过测试反馈改进开发过程\n4. 质量评估：提供软件质量的客观度量信息\n5. 降低风险：减少软件上线后出现问题的风险\n\n注意：测试不能证明软件没有缺陷，只能证明缺陷存在。测试是质量保障的重要手段，但不是唯一手段。",
    },
    {
        "title": "请描述软件测试生命周期（STLC）的各阶段",
        "category": "测试基础",
        "difficulty": "easy",
        "description": "简述软件测试生命周期的完整流程。",
        "answer": "软件测试生命周期（STLC）包括以下阶段：\n\n1. 需求分析：分析需求文档，确定测试范围，识别可测试性需求\n2. 测试计划：制定测试策略、估算工作量、分配资源、确定进度\n3. 测试设计：设计测试用例、准备测试数据、编写测试脚本\n4. 测试环境搭建：配置硬件、软件、网络环境，部署被测系统\n5. 测试执行：执行测试用例，记录实际结果，提交缺陷\n6. 缺陷管理：跟踪缺陷状态，验证修复，回归测试\n7. 测试报告：汇总测试结果，评估质量，给出上线建议\n\n每个阶段都有明确的入口准则和出口准则。",
    },
    {
        "title": "什么是回归测试？什么时候需要做回归测试？",
        "category": "测试基础",
        "difficulty": "easy",
        "description": "解释回归测试的概念和触发时机。",
        "answer": "回归测试是在软件修改后重新执行之前通过的测试用例，确认修改没有引入新缺陷或影响已有功能。\n\n触发时机：\n1. 代码修改后：新功能开发或缺陷修复后\n2. 需求变更后：需求调整导致代码改动\n3. 环境变更后：操作系统、数据库、中间件升级\n4. 版本合并后：多人协作代码合并时\n5. 定期执行：作为每日构建的一部分\n\n回归测试策略：\n- 全量回归：重新执行所有用例（最安全但耗时）\n- 选择性回归：只执行受影响的用例（推荐）\n- 基于风险的回归：优先回归高风险模块",
    },
    {
        "title": "V模型和W模型有什么区别？",
        "category": "测试基础",
        "difficulty": "medium",
        "description": "对比V模型和W模型的特点和适用场景。",
        "answer": "V模型：\n- 测试与开发阶段一一对应：需求→验收测试，概要设计→系统测试，详细设计→集成测试，编码→单元测试\n- 特点：强调测试与开发的对应关系，结构清晰\n- 缺点：测试是开发之后的活动，需求缺陷发现较晚\n\nW模型：\n- 在V模型基础上增加了同步测试：需求分析↔需求测试，概要设计↔概要测试...\n- 特点：测试与开发同步进行，贯穿整个生命周期\n- 优点：符合'尽早测试'原则，能在需求阶段就发现缺陷\n- 包括静态测试（评审、走查）和动态测试\n\n适用场景：\n- V模型：需求稳定的项目\n- W模型：需求复杂、质量要求高的项目（推荐）",
    },
    {
        "title": "黑盒测试和白盒测试有什么区别？各有哪些方法？",
        "category": "测试基础",
        "difficulty": "easy",
        "description": "对比黑盒测试和白盒测试的概念、方法和适用场景。",
        "answer": "黑盒测试（功能测试）：\n- 不考虑内部结构，只关注输入输出\n- 基于需求规格说明设计用例\n- 方法：等价类划分、边界值分析、因果图、判定表、状态迁移图、场景法\n- 适用：系统测试、验收测试\n- 优点：从用户角度出发，不需要了解代码\n\n白盒测试（结构测试）：\n- 关注内部逻辑结构，需要了解代码\n- 基于代码结构设计用例\n- 方法：语句覆盖、判定覆盖、条件覆盖、条件组合覆盖、路径覆盖\n- 适用：单元测试、集成测试\n- 优点：覆盖率高，能发现代码级缺陷\n\n灰盒测试：\n- 介于黑盒和白盒之间\n- 关注输入输出，也关注内部工作原理\n- 适用：接口测试、数据库测试",
    },
    {
        "title": "什么是测试左移和测试右移？",
        "category": "测试基础",
        "difficulty": "hard",
        "description": "解释测试左移和测试右移的概念和实践方法。",
        "answer": "测试左移（Shift Left）：\n- 将测试活动前移到需求和设计阶段\n- 核心理念：尽早发现缺陷，修复成本最低\n- 实践方法：\n  1. 需求评审：参与需求评审，发现需求缺陷\n  2. 设计评审：参与架构和详细设计评审\n  3. TDD：测试驱动开发，先写测试再写代码\n  4. 静态分析：使用SonarQube等工具进行代码扫描\n  5. 代码审查：在Code Review中关注测试质量\n\n测试右移（Shift Right）：\n- 将测试延伸到生产环境\n- 核心理念：真实环境中验证系统行为\n- 实践方法：\n  1. 灰度发布：小范围验证新版本\n  2. A/B测试：对比不同版本效果\n  3. 监控告警：实时监控系统健康状态\n  4. 混沌工程：主动注入故障验证系统韧性\n  5. 用户反馈：收集真实用户使用数据",
    },
    {
        "title": "什么是测试金字塔？如何合理分配测试比例？",
        "category": "测试基础",
        "difficulty": "medium",
        "description": "解释测试金字塔模型和测试分层策略。",
        "answer": "测试金字塔模型（Mike Cohn提出）：\n\n层次结构（从下到上）：\n1. 单元测试（底层，数量最多）：测试单个函数/方法，速度快，成本低\n2. 集成测试（中层）：测试模块间交互，包括API测试、服务集成\n3. 端到端测试（顶层，数量最少）：测试完整业务流程，速度慢，成本高\n\n推荐比例：\n- 单元测试：70%（快速反馈，覆盖核心逻辑）\n- 集成测试：20%（验证接口和数据流）\n- 端到端测试：10%（验证关键业务场景）\n\n反模式：\n- 冰淇淋蛋卷：大量手工测试，少量自动化\n- 倒金字塔：大量E2E测试，缺少单元测试\n- 沙漏：大量单元和E2E，缺少集成测试\n\n原则：尽量用低层测试覆盖，减少高层测试数量。",
    },
    {
        "title": "Alpha测试和Beta测试有什么区别？",
        "category": "测试基础",
        "difficulty": "medium",
        "description": "对比Alpha测试和Beta测试的特点。",
        "answer": "Alpha测试：\n- 场所：公司内部或受控环境\n- 人员：公司内部员工或受信任的用户\n- 环境：受控的测试环境\n- 目的：在发布前发现潜在问题\n- 特点：开发人员可以在场，问题可以立即修复\n\nBeta测试：\n- 场所：用户实际使用环境\n- 人员：真实用户（外部）\n- 环境：不受控的真实环境\n- 目的：收集真实用户反馈，发现实际使用中的问题\n- 特点：开发人员不在场，问题需要后续版本修复\n\n区别总结：\n| 维度 | Alpha | Beta |\n|------|-------|------|\n| 环境 | 受控 | 不受控 |\n| 人员 | 内部 | 外部用户 |\n| 阶段 | Beta之前 | Alpha之后 |\n| 控制 | 高度控制 | 自由使用 |\n| 反馈 | 即时 | 异步收集 |",
    },
]

TEST_CASE_DESIGN = [
    {
        "title": "什么是等价类划分法？请举例说明",
        "category": "测试用例设计",
        "difficulty": "easy",
        "description": "解释等价类划分法的概念并给出实例。",
        "answer": "等价类划分是将输入域划分为若干等价类，从每个等价类中选取代表值进行测试。\n\n分类：\n1. 有效等价类：符合需求的输入数据\n2. 无效等价类：不符合需求的输入数据\n\n示例：年龄输入框要求18-60岁\n- 有效等价类：25（代表18-60之间的整数）\n- 无效等价类：\n  - 10（代表<18的数值）\n  - 70（代表>60的数值）\n  - abc（代表非数字输入）\n  - 空值（代表未输入）\n  - -5（代表负数）\n\n设计步骤：\n1. 分析输入条件\n2. 划分有效等价类和无效等价类\n3. 为每个等价类选取代表值\n4. 设计测试用例",
    },
    {
        "title": "边界值分析法的原理是什么？为什么边界处容易出错？",
        "category": "测试用例设计",
        "difficulty": "easy",
        "description": "解释边界值分析法的原理和常见边界错误。",
        "answer": "边界值分析法：对输入或输出的边界值进行测试的方法。\n\n原理：缺陷往往集中在边界附近，因为：\n1. 边界条件判断容易出错（< vs <=）\n2. 循环边界处理不当（off-by-one错误）\n3. 数组越界访问\n4. 数据类型溢出\n\n测试点：\n- 上点：边界上的点\n- 内点：边界内的点\n- 离点：边界外的点\n\n示例：输入范围[1, 100]\n- 测试值：0, 1, 2, 99, 100, 101\n- 重点测试边界值1和100及其邻近值\n\n与等价类划分配合使用：\n- 等价类划分确定测试范围\n- 边界值分析确定重点测试点\n- 两者结合提高测试覆盖率",
    },
    {
        "title": "什么是判定表法？适用于什么场景？",
        "category": "测试用例设计",
        "difficulty": "medium",
        "description": "解释判定表法的概念和使用方法。",
        "answer": "判定表法：分析和表达多逻辑条件下执行不同操作的工具。\n\n组成：\n1. 条件桩：列出所有条件\n2. 动作桩：列出所有操作\n3. 条件项：条件的取值组合\n4. 动作项：对应的操作\n\n适用场景：\n- 多个输入条件的组合\n- 条件之间有逻辑关系\n- 不同条件组合对应不同操作\n\n示例：订单优惠规则\n- 条件：VIP会员、订单金额>500、新用户\n- 动作：9折、满减、免运费、送积分\n\n设计步骤：\n1. 识别条件和动作\n2. 构建判定表\n3. 简化判定表（合并相同规则）\n4. 为每条规则设计测试用例",
    },
    {
        "title": "什么是状态迁移图法？如何设计测试用例？",
        "category": "测试用例设计",
        "difficulty": "medium",
        "description": "解释状态迁移图法的概念和应用。",
        "answer": "状态迁移图法：分析系统状态变化来设计测试用例的方法。\n\n适用场景：\n- 系统有明确的状态定义\n- 状态之间有迁移条件\n- 不同状态下行为不同\n\n示例：订单状态\n- 状态：待支付→已支付→已发货→已完成→已取消\n- 迁移条件：支付成功、发货、确认收货、超时取消\n\n设计步骤：\n1. 识别所有状态\n2. 绘制状态迁移图\n3. 识别迁移条件\n4. 设计覆盖所有迁移路径的测试用例\n5. 考虑异常状态迁移\n\n覆盖标准：\n- 状态覆盖：覆盖所有状态\n- 迁移覆盖：覆盖所有迁移路径\n- 全覆盖：覆盖所有状态和迁移的组合",
    },
    {
        "title": "什么是场景法？如何设计测试用例？",
        "category": "测试用例设计",
        "difficulty": "medium",
        "description": "解释场景法的概念和设计步骤。",
        "answer": "场景法：基于业务流程设计测试用例的方法，也叫流程分析法。\n\n核心思想：模拟用户的实际操作流程，设计端到端的测试场景。\n\n设计步骤：\n1. 分析业务流程，绘制流程图\n2. 识别基本流（正常流程）\n3. 识别备选流（分支流程）\n4. 识别异常流（错误处理流程）\n5. 为每个场景设计测试用例\n\n示例：电商下单流程\n- 基本流：浏览→加入购物车→提交订单→支付→完成\n- 备选流：使用优惠券、修改地址、选择配送方式\n- 异常流：库存不足、支付失败、网络中断\n\n优点：覆盖业务场景全面，贴近用户实际使用\n缺点：场景复杂时用例数量爆炸",
    },
    {
        "title": "什么是错误推测法？如何应用？",
        "category": "测试用例设计",
        "difficulty": "medium",
        "description": "解释错误推测法的概念和常见错误类型。",
        "answer": "错误推测法：基于经验和直觉推测程序中可能存在的错误，有针对性地设计测试用例。\n\n基于经验推测的常见错误类型：\n1. 输入相关：空值、超长输入、特殊字符、SQL注入、XSS\n2. 边界相关：临界值、溢出、精度丢失\n3. 并发相关：竞态条件、死锁、数据不一致\n4. 网络相关：超时、断网、重试、幂等性\n5. 数据相关：数据类型转换、编码问题、时区问题\n6. 状态相关：并发操作、状态回滚、数据一致性\n\n应用方法：\n1. 列出可能的错误场景\n2. 设计触发这些场景的测试用例\n3. 与等价类、边界值结合使用\n4. 在探索性测试中重点应用\n\n优点：能发现其他方法遗漏的缺陷\n缺点：依赖测试人员经验，不够系统化",
    },
]

DEFECT_MANAGEMENT = [
    {
        "title": "缺陷严重程度和优先级有什么区别？",
        "category": "缺陷管理",
        "difficulty": "easy",
        "description": "解释缺陷严重程度和优先级的概念及区别。",
        "answer": "严重程度（Severity）：\n- 定义：缺陷对系统功能影响的程度\n- 分类：致命、严重、一般、轻微\n- 特点：客观的，由缺陷本身决定\n- 示例：系统崩溃（致命）、功能错误（严重）、界面问题（轻微）\n\n优先级（Priority）：\n- 定义：缺陷修复的紧急程度\n- 分类：高、中、低\n- 特点：主观的，受业务影响\n- 示例：首页崩溃（高）、边缘功能错误（低）\n\n关键区别：\n- 严重程度高的缺陷优先级不一定高（如：边缘功能崩溃）\n- 严重程度低的缺陷优先级可能高（如：首页拼写错误）\n- 两者独立评估，没有必然对应关系",
    },
    {
        "title": "缺陷的生命周期是怎样的？",
        "category": "缺陷管理",
        "difficulty": "easy",
        "description": "描述缺陷从发现到关闭的完整生命周期。",
        "answer": "缺陷生命周期：\n\n新建（New）→已分配（Open）→已修复（Fixed）→已验证（Verified）→已关闭（Closed）\n\n扩展状态：\n- 重新打开（Reopened）：验证不通过，重新激活\n- 已拒绝（Rejected）：非缺陷或不修复\n- 延期（Deferred）：推迟到后续版本修复\n- 已挂起（Suspended）：暂时挂起\n\n关键角色：\n- 测试人员：发现、提交、验证缺陷\n- 开发人员：分析、修复缺陷\n- 项目经理：评估优先级、决定是否修复\n\n最佳实践：\n- 缺陷描述清晰，步骤可重现\n- 及时更新缺陷状态\n- 修复后必须回归验证",
    },
    {
        "title": "如何描述一个高质量的缺陷报告？",
        "category": "缺陷管理",
        "difficulty": "medium",
        "description": "说明缺陷报告的关键要素和写作规范。",
        "answer": "高质量缺陷报告要素：\n\n1. 标题：简明扼要描述问题\n   - 好：'登录页面输入正确密码后提示密码错误'\n   - 坏：'登录有问题'\n\n2. 环境信息：操作系统、浏览器、版本号\n3. 前置条件：测试前需要满足的条件\n4. 重现步骤：详细的操作步骤（1,2,3...）\n5. 预期结果：应该出现的正确行为\n6. 实际结果：实际出现的错误行为\n7. 严重程度：致命/严重/一般/轻微\n8. 优先级：高/中/低\n9. 附件：截图、日志、视频\n\n写作原则：\n- 准确：描述准确，不夸大不缩小\n- 清晰：步骤清晰，易于重现\n- 完整：信息完整，减少沟通成本\n- 客观：描述事实，不做主观判断",
    },
]

COMPUTER_BASICS = [
    {
        "title": "HTTP协议中GET和POST请求有什么区别？",
        "category": "计算机基础",
        "difficulty": "easy",
        "description": "解释HTTP GET和POST方法的主要区别。",
        "answer": "GET和POST的区别：\n\n1. 参数位置：GET参数在URL中可见，POST参数在请求体中\n2. 数据长度：GET有URL长度限制（约2KB），POST理论上没有限制\n3. 安全性：GET参数暴露在URL中，POST相对安全（但仍需HTTPS）\n4. 缓存：GET可被缓存、收藏、保留在历史记录，POST不能\n5. 幂等性：GET是幂等的（多次请求结果相同），POST不是\n6. 用途：GET用于获取数据，POST用于提交/修改数据\n7. 编码：GET只支持URL编码，POST支持多种编码方式\n\n实际应用：\n- 查询参数用GET（搜索、筛选）\n- 提交表单用POST（登录、注册、上传）\n- 敏感数据必须用POST+HTTPS",
    },
    {
        "title": "Cookie和Session有什么区别？",
        "category": "计算机基础",
        "difficulty": "medium",
        "description": "对比Cookie和Session的机制和适用场景。",
        "answer": "Cookie：\n- 存储位置：客户端（浏览器）\n- 数据大小：限制4KB\n- 安全性：较低，可被用户查看和修改\n- 生命周期：可设置过期时间，持久化存储\n- 传输：每次HTTP请求自动携带\n\nSession：\n- 存储位置：服务端\n- 数据大小：没有限制\n- 安全性：较高，用户无法直接访问\n- 生命周期：浏览器关闭或超时后失效\n- 传输：通过Cookie中的SessionID关联\n\n工作机制：\n1. 用户首次访问，服务端创建Session\n2. 服务端将SessionID通过Cookie发送给客户端\n3. 客户端后续请求携带SessionID\n4. 服务端根据SessionID获取Session数据\n\n适用场景：\n- Cookie：记住密码、个性化设置、跟踪分析\n- Session：用户登录状态、购物车、表单数据",
    },
    {
        "title": "TCP三次握手和四次挥手的过程是什么？",
        "category": "计算机基础",
        "difficulty": "medium",
        "description": "描述TCP连接建立和断开的过程。",
        "answer": "三次握手（建立连接）：\n1. 客户端→服务端：SYN=1, seq=x（请求建立连接）\n2. 服务端→客户端：SYN=1, ACK=1, seq=y, ack=x+1（同意建立连接）\n3. 客户端→服务端：ACK=1, seq=x+1, ack=y+1（确认连接建立）\n\n为什么三次：防止失效的连接请求到达服务端造成资源浪费\n\n四次挥手（断开连接）：\n1. 客户端→服务端：FIN=1（请求断开）\n2. 服务端→客户端：ACK=1（收到请求，但可能还有数据要发）\n3. 服务端→客户端：FIN=1（数据发完，同意断开）\n4. 客户端→服务端：ACK=1（确认断开）\n\n为什么四次：TCP是全双工，需要分别关闭两个方向的连接\n\n测试中的应用：\n- 网络抓包分析（Wireshark）\n- 排查连接超时问题\n- 理解HTTP Keep-Alive机制",
    },
]

# ============================================================
# Stage 2: 功能测试精通
# ============================================================

FUNCTIONAL_TEST = [
    {
        "title": "如何测试一个登录功能？请列出测试点",
        "category": "功能测试",
        "difficulty": "medium",
        "description": "设计登录功能的完整测试方案。",
        "answer": "登录功能测试点：\n\n功能测试：\n1. 正确账号密码登录成功\n2. 错误密码提示错误\n3. 空用户名/空密码提示\n4. 特殊字符输入处理\n5. 大小写敏感性\n6. 记住密码功能\n7. 自动登录功能\n8. 退出登录功能\n\n安全测试：\n1. SQL注入防护\n2. XSS攻击防护\n3. 暴力破解防护（账号锁定）\n4. 密码传输加密\n5. 验证码功能\n\n可用性测试：\n1. Tab键切换\n2. 回车键提交\n3. 错误提示清晰\n4. 密码可见性切换\n\n兼容性：\n1. 不同浏览器\n2. 不同设备（PC/手机）\n3. 不同操作系统\n\n性能：\n1. 高并发登录\n2. 响应时间",
    },
    {
        "title": "如何进行购物车功能的测试？",
        "category": "功能测试",
        "difficulty": "medium",
        "description": "设计购物车功能的测试用例。",
        "answer": "购物车功能测试：\n\n基础功能：\n1. 添加商品到购物车\n2. 修改商品数量\n3. 删除商品\n4. 清空购物车\n5. 商品价格计算\n6. 优惠券应用\n\n边界测试：\n1. 数量为0时的行为\n2. 超大数量（超过库存）\n3. 购物车商品数量上限\n4. 价格精度（小数点）\n\n异常场景：\n1. 商品下架后购物车显示\n2. 价格变动后购物车更新\n3. 库存不足时的提示\n4. 网络中断时的本地缓存\n5. 多设备同步\n\n性能测试：\n1. 大量商品时的加载速度\n2. 并发修改购物车",
    },
    {
        "title": "什么是冒烟测试？与回归测试有什么区别？",
        "category": "功能测试",
        "difficulty": "easy",
        "description": "解释冒烟测试的概念和与其他测试类型的区别。",
        "answer": "冒烟测试（Smoke Testing）：\n- 定义：对软件基本功能进行初步验证，确认主要功能是否正常\n- 目的：快速验证版本是否可测，决定是否进行更深入的测试\n- 范围：核心功能的主路径\n- 时机：每个新版本构建后首先执行\n\n与回归测试的区别：\n| 维度 | 冒烟测试 | 回归测试 |\n|------|----------|----------|\n| 范围 | 核心功能 | 所有相关功能 |\n| 深度 | 浅层验证 | 深入测试 |\n| 时间 | 短（30分钟内） | 长（数小时） |\n| 时机 | 版本构建后 | 修改后 |\n| 目的 | 是否可测 | 是否引入新缺陷 |\n\n最佳实践：\n- 冒烟测试用例应自动化\n- 冒烟测试失败则打回版本\n- 回归测试应选择性执行",
    },
    {
        "title": "如何测试一个文件上传功能？",
        "category": "功能测试",
        "difficulty": "medium",
        "description": "设计文件上传功能的测试方案。",
        "answer": "文件上传测试点：\n\n功能测试：\n1. 正常文件上传成功\n2. 支持的文件格式（PDF、图片、文档等）\n3. 上传进度显示\n4. 上传成功后文件可访问\n5. 多文件同时上传\n\n边界测试：\n1. 最大文件大小限制\n2. 最小文件大小（0字节）\n3. 文件名特殊字符\n4. 文件名长度限制\n5. 超长路径\n\n异常测试：\n1. 不支持的文件格式\n2. 超过大小限制\n3. 上传过程中网络中断\n4. 上传过程中取消\n5. 磁盘空间不足\n6. 重复文件名处理\n\n安全测试：\n1. 恶意文件上传（病毒）\n2. 文件名注入攻击\n3. 路径遍历攻击\n4. 文件类型伪造",
    },
]

WEB_TEST = [
    {
        "title": "如何测试一个搜索功能？",
        "category": "Web测试",
        "difficulty": "medium",
        "description": "设计搜索功能的测试方案。",
        "answer": "搜索功能测试：\n\n功能测试：\n1. 关键词搜索返回正确结果\n2. 空搜索处理\n3. 搜索结果排序（相关性、时间、热度）\n4. 分页功能\n5. 搜索结果高亮\n6. 搜索历史记录\n7. 热门搜索推荐\n\n输入测试：\n1. 特殊字符输入\n2. 超长关键词\n3. 空格处理\n4. SQL注入/XSS防护\n5. 中英文混合\n6. 模糊搜索\n\n性能测试：\n1. 大数据量搜索速度\n2. 并发搜索\n3. 搜索结果加载时间\n\n用户体验：\n1. 搜索建议/自动补全\n2. 无结果时的提示\n3. 搜索结果展示清晰",
    },
    {
        "title": "如何测试分页功能？",
        "category": "Web测试",
        "difficulty": "medium",
        "description": "设计分页功能的测试方案。",
        "answer": "分页功能测试：\n\n功能测试：\n1. 首页数据正确加载\n2. 点击下一页/上一页\n3. 跳转到指定页\n4. 每页显示数量切换\n5. 总页数显示正确\n6. 总记录数显示正确\n\n边界测试：\n1. 第一页时上一页按钮禁用\n2. 最后一页时下一页按钮禁用\n3. 只有一页时分页控件隐藏\n4. 输入超出范围的页码\n5. 输入非数字页码\n6. 每页数量为0或负数\n\n数据一致性：\n1. 切换页码后数据不重复\n2. 切换页码后数据不遗漏\n3. 数据更新后分页总数同步\n4. 快速连续翻页不报错\n\n性能：\n1. 大数据量分页加载速度\n2. 深分页（第10000页）性能",
    },
]

# ============================================================
# Stage 3: 测试技术进阶
# ============================================================

API_TEST = [
    {
        "title": "什么是接口测试？接口测试的重点是什么？",
        "category": "接口测试",
        "difficulty": "medium",
        "description": "解释接口测试的概念和测试重点。",
        "answer": "接口测试：对系统间接口进行测试，验证接口的正确性、稳定性和安全性。\n\n测试重点：\n1. 参数校验：必填参数、类型、长度、范围、边界值\n2. 业务逻辑：接口功能是否符合需求\n3. 返回值：状态码、数据格式、字段完整性\n4. 异常处理：错误参数、异常场景的错误提示\n5. 幂等性：同一请求多次执行结果相同\n6. 安全性：认证授权、数据加密、SQL注入\n7. 性能：响应时间、并发处理能力\n8. 兼容性：新旧版本接口兼容\n\n常用工具：Postman、JMeter、Requests+Pytest\n\n测试方法：\n- 正向测试：正常参数验证功能\n- 反向测试：异常参数验证容错\n- 组合测试：多参数组合验证",
    },
    {
        "title": "什么是RESTful API？设计原则是什么？",
        "category": "接口测试",
        "difficulty": "medium",
        "description": "解释RESTful API的概念和设计原则。",
        "answer": "REST（Representational State Transfer）是一种软件架构风格。\n\n核心原则：\n1. 资源导向：URL用名词表示资源（/users, /orders）\n2. HTTP方法语义化：\n   - GET：获取资源\n   - POST：创建资源\n   - PUT：更新资源（全量）\n   - PATCH：更新资源（部分）\n   - DELETE：删除资源\n3. 无状态：每个请求包含所有必要信息\n4. 统一接口：一致的URL设计和响应格式\n5. 分层系统：客户端无需了解中间层\n\n设计规范：\n- URL使用小写字母和连字符\n- 版本号放在URL中（/api/v1/users）\n- 使用HTTP状态码表示结果\n- 响应使用JSON格式\n- 支持分页、过滤、排序\n\n示例：\n- GET /api/v1/users（获取列表）\n- POST /api/v1/users（创建）\n- GET /api/v1/users/1（获取详情）\n- PUT /api/v1/users/1（更新）\n- DELETE /api/v1/users/1（删除）",
    },
    {
        "title": "JWT Token的工作原理是什么？如何测试？",
        "category": "接口测试",
        "difficulty": "medium",
        "description": "解释JWT的结构、工作流程和测试要点。",
        "answer": "JWT（JSON Web Token）结构：\n1. Header：算法和类型（{\"alg\":\"HS256\",\"typ\":\"JWT\"}）\n2. Payload：用户信息和声明（{\"sub\":\"123\",\"name\":\"John\",\"exp\":1234567890}）\n3. Signature：签名（Header+Payload+Secret的HMAC SHA256）\n\n工作流程：\n1. 用户登录，服务端验证凭据\n2. 服务端生成JWT返回给客户端\n3. 客户端存储JWT（localStorage/Cookie）\n4. 后续请求在Authorization头携带JWT\n5. 服务端验证JWT签名和过期时间\n\n测试要点：\n1. 正常Token验证通过\n2. 过期Token被拒绝\n3. 篡改Token被拒绝\n4. 空Token被拒绝\n5. 不同用户Token隔离\n6. Token刷新机制\n7. 并发请求Token一致性",
    },
    {
        "title": "如何测试接口的幂等性？",
        "category": "接口测试",
        "difficulty": "hard",
        "description": "解释接口幂等性的概念和测试方法。",
        "answer": "幂等性定义：同一请求执行一次和多次，结果相同。\n\nHTTP方法幂等性：\n- GET：幂等（多次查询结果相同）\n- PUT：幂等（多次更新结果相同）\n- DELETE：幂等（多次删除结果相同）\n- POST：非幂等（多次创建会创建多条记录）\n\n测试方法：\n1. 重复提交测试：\n   - 连续点击提交按钮\n   - 网络重试场景\n   - 前端防重+后端校验\n\n2. 并发测试：\n   - 多线程同时提交相同请求\n   - 验证数据一致性\n\n3. 特殊场景：\n   - 支付接口重复支付\n   - 订单接口重复下单\n   - 转账接口重复转账\n\n保证幂等性的方式：\n- 唯一请求ID\n- 唯一约束\n- 乐观锁/悲观锁\n- Token机制\n- 状态机控制",
    },
    {
        "title": "接口测试中如何处理签名认证？",
        "category": "接口测试",
        "difficulty": "hard",
        "description": "说明接口签名认证的原理和测试方法。",
        "answer": "签名认证原理：\n1. 客户端将请求参数按规则排序\n2. 拼接参数字符串+密钥\n3. 使用MD5/SHA256等算法生成签名\n4. 将签名放在请求头或参数中\n5. 服务端用相同规则验证签名\n\n签名规则示例：\n1. 参数按字母顺序排序\n2. 用&拼接key=value\n3. 末尾拼接&secret=密钥\n4. 对整个字符串做MD5\n\n测试要点：\n1. 正常签名验证通过\n2. 篡改参数后签名失效\n3. 签名过期时间验证\n4. 时间戳偏移处理\n5. 重放攻击防护\n6. 不同密钥签名隔离\n\n自动化测试实现：\n- 在测试工具中实现签名算法\n- 使用Pre-request Script动态生成签名\n- 封装签名生成函数复用",
    },
]

LINUX_TEST = [
    {
        "title": "Linux常用命令有哪些？请分类说明",
        "category": "Linux",
        "difficulty": "easy",
        "description": "列举测试中常用的Linux命令。",
        "answer": "文件操作：\n- ls：列出文件（-l详细，-a隐藏文件）\n- cd：切换目录\n- cp：复制文件\n- mv：移动/重命名\n- rm：删除（-rf强制递归）\n- mkdir：创建目录\n- find：查找文件\n- cat/less/tail：查看文件内容\n\n进程管理：\n- ps：查看进程（ps aux）\n- top：实时监控\n- kill：终止进程（-9强制）\n- nohup：后台运行\n\n网络相关：\n- curl：HTTP请求\n- wget：下载文件\n- netstat/ss：查看端口\n- ping：网络连通性\n- telnet：端口连通性\n\n日志分析：\n- tail -f：实时查看日志\n- grep：搜索日志内容\n- awk：文本处理\n- wc -l：统计行数\n\n权限管理：\n- chmod：修改权限\n- chown：修改所有者\n- sudo：管理员权限",
    },
    {
        "title": "如何用Shell脚本实现日志分析？",
        "category": "Linux",
        "difficulty": "medium",
        "description": "编写Shell脚本分析日志文件的常见场景。",
        "answer": "日志分析常见场景：\n\n1. 统计错误日志数量：\n```bash\ngrep -c 'ERROR' /var/log/app.log\n```\n\n2. 按时间范围筛选日志：\n```bash\nsed -n '/2024-01-01 10:00/,/2024-01-01 11:00/p' app.log\n```\n\n3. 统计HTTP状态码分布：\n```bash\nawk '{print $9}' access.log | sort | uniq -c | sort -rn\n```\n\n4. 查找TOP10慢请求：\n```bash\nsort -t'=' -k2 -rn access.log | head -10\n```\n\n5. 实时监控错误日志：\n```bash\ntail -f app.log | grep --line-buffered 'ERROR'\n```\n\n6. 统计每小时请求数：\n```bash\nawk '{print substr($4,2,13)}' access.log | uniq -c\n```\n\n7. 查找特定IP的请求：\n```bash\ngrep '192.168.1.1' access.log | wc -l\n```",
    },
    {
        "title": "如何排查Linux服务器上的内存泄漏问题？",
        "category": "Linux",
        "difficulty": "hard",
        "description": "描述排查内存泄漏的步骤和工具。",
        "answer": "内存泄漏排查步骤：\n\n1. 确认内存使用情况：\n```bash\nfree -h          # 查看整体内存\ntop -o %MEM      # 按内存排序查看进程\nps aux --sort=-%mem | head -10\n```\n\n2. 监控内存增长趋势：\n```bash\n# 使用vmstat每秒采样\nvmstat 1 10\n# 使用pidstat监控特定进程\npidstat -r -p <PID> 1\n```\n\n3. 分析进程内存：\n```bash\n# 查看进程内存映射\npmap -x <PID>\n# 查看/proc文件系统\ncat /proc/<PID>/status | grep VmRSS\n```\n\n4. Java应用排查：\n```bash\njmap -heap <PID>           # 查看堆内存\njmap -histo <PID> | head -20  # 查看对象分布\njstat -gc <PID> 1000       # GC监控\n```\n\n5. 生成堆转储分析：\n```bash\njmap -dump:format=b,file=heap.bin <PID>\n# 使用MAT或VisualVM分析\n```\n\n常见原因：\n- 未关闭的资源（文件、连接）\n- 缓存未设置上限\n- 全局变量持续增长\n- 线程泄漏",
    },
]

DATABASE_TEST = [
    {
        "title": "什么是SQL注入？如何测试和防御？",
        "category": "数据库",
        "difficulty": "medium",
        "description": "解释SQL注入的原理、测试方法和防御措施。",
        "answer": "SQL注入原理：通过在输入中插入恶意SQL代码，改变原始SQL语义，实现非授权操作。\n\n测试方法：\n1. 输入单引号测试：' → 观察是否报错\n2. 逻辑测试：' OR '1'='1 → 绕过登录\n3. 联合查询：' UNION SELECT * FROM users --\n4. 时间盲注：' AND SLEEP(5) --\n5. 使用SQLMap自动化测试\n\n常见注入点：\n- 登录表单\n- 搜索框\n- URL参数\n- Cookie值\n- HTTP头\n\n防御措施：\n1. 参数化查询/预编译语句（最重要）\n2. 输入验证和过滤\n3. 最小权限原则\n4. WAF（Web应用防火墙）\n5. 错误信息不暴露数据库细节\n6. ORM框架（自动防注入）",
    },
    {
        "title": "如何进行数据库查询优化？",
        "category": "数据库",
        "difficulty": "hard",
        "description": "说明SQL查询优化的方法和最佳实践。",
        "answer": "查询优化方法：\n\n1. 使用EXPLAIN分析执行计划：\n```sql\nEXPLAIN SELECT * FROM users WHERE name = 'test';\n```\n关注：type（ALL/index/range/ref/const）、rows、Extra\n\n2. 索引优化：\n- 为WHERE、JOIN、ORDER BY字段创建索引\n- 避免在索引列上使用函数\n- 使用复合索引（最左前缀原则）\n- 避免过多索引（影响写入性能）\n\n3. 查询优化：\n- 避免SELECT *，只查需要的字段\n- 使用LIMIT限制结果集\n- 避免在WHERE中使用!=、NOT IN\n- 使用JOIN代替子查询\n- 避免使用OR（改用UNION）\n\n4. 表结构优化：\n- 选择合适的数据类型\n- 正规化与反正规化平衡\n- 分区表（大表）\n\n5. 慢查询分析：\n```sql\nSET GLOBAL slow_query_log = 1;\nSET GLOBAL long_query_time = 1;\n```",
    },
    {
        "title": "什么是数据库事务？事务的ACID特性是什么？",
        "category": "数据库",
        "difficulty": "medium",
        "description": "解释数据库事务和ACID特性。",
        "answer": "事务（Transaction）：一组数据库操作，要么全部成功，要么全部失败。\n\nACID特性：\n1. 原子性（Atomicity）：\n   - 事务是不可分割的工作单位\n   - 要么全部执行，要么全部不执行\n   - 失败时回滚到事务开始前的状态\n\n2. 一致性（Consistency）：\n   - 事务执行前后，数据库从一个一致状态到另一个一致状态\n   - 所有约束、触发器、规则都必须满足\n\n3. 隔离性（Isolation）：\n   - 多个事务并发执行时，互不干扰\n   - 隔离级别：读未提交、读已提交、可重复读、串行化\n\n4. 持久性（Durability）：\n   - 事务提交后，对数据库的改变是永久的\n   - 即使系统故障也不会丢失\n\n测试中的应用：\n- 验证事务提交和回滚\n- 测试并发事务的数据一致性\n- 测试不同隔离级别下的行为",
    },
]

PERFORMANCE_TEST = [
    {
        "title": "性能测试有哪些类型？各有什么目的？",
        "category": "性能测试",
        "difficulty": "medium",
        "description": "区分不同类型的性能测试。",
        "answer": "性能测试类型：\n\n1. 负载测试（Load Testing）：\n   - 目的：逐步增加负载，找到系统最佳性能点\n   - 关注：响应时间、吞吐量、资源利用率\n\n2. 压力测试（Stress Testing）：\n   - 目的：超负载运行，验证系统恢复能力\n   - 关注：系统极限、降级策略、数据完整性\n\n3. 稳定性测试（Soak Testing）：\n   - 目的：长时间运行，检测内存泄漏等问题\n   - 关注：内存增长、连接泄漏、性能衰减\n\n4. 容量测试（Capacity Testing）：\n   - 目的：确定系统最大处理能力\n   - 关注：最大并发数、最大数据量\n\n5. 基准测试（Benchmark Testing）：\n   - 目的：建立性能基线\n   - 关注：标准配置下的性能指标\n\n关键指标：\n- TPS（每秒事务数）\n- RT（响应时间）\n- 并发用户数\n- 错误率\n- 资源利用率（CPU、内存、网络）",
    },
    {
        "title": "TPS上不去可能是什么原因？如何排查？",
        "category": "性能测试",
        "difficulty": "hard",
        "description": "分析TPS瓶颈的可能原因和排查思路。",
        "answer": "TPS上不去的常见原因：\n\n1. 应用层：\n   - 线程池不足\n   - 连接池耗尽\n   - 代码锁竞争\n   - 同步阻塞调用\n   - GC频繁（Java应用）\n\n2. 数据库层：\n   - 慢SQL查询\n   - 索引缺失\n   - 连接池不足\n   - 死锁\n   - 锁等待\n\n3. 中间件层：\n   - 消息队列积压\n   - 缓存击穿/雪崩\n   - 负载均衡配置不当\n\n4. 系统层：\n   - CPU饱和\n   - 内存不足\n   - 磁盘I/O瓶颈\n   - 网络带宽不足\n\n排查思路：\n1. 先看监控（CPU/内存/网络/磁盘）\n2. 再看中间件（连接池/线程池/队列）\n3. 最后看代码（慢查询/锁/阻塞）\n4. 分层定位，逐层排查\n\n工具：top、vmstat、iostat、netstat、jstack、jmap",
    },
]

# ============================================================
# Stage 4: 自动化测试专家
# ============================================================

PYTHON_PROGRAMMING = [
    {
        "title": "Python中的列表和元组有什么区别？",
        "category": "Python编程",
        "difficulty": "easy",
        "description": "对比Python列表和元组的特点。",
        "answer": "列表（List）vs 元组（Tuple）：\n\n1. 可变性：\n   - 列表：可变（可以修改、添加、删除元素）\n   - 元组：不可变（创建后不能修改）\n\n2. 语法：\n   - 列表：[1, 2, 3]\n   - 元组：(1, 2, 3)\n\n3. 性能：\n   - 元组比列表快（不可变，内存更紧凑）\n   - 元组可以作为字典的key，列表不行\n\n4. 使用场景：\n   - 列表：需要修改的集合（用户列表、配置项）\n   - 元组：不可变数据（坐标、数据库记录、函数返回值）\n\n5. 方法：\n   - 列表：append、extend、insert、remove、pop、sort\n   - 元组：count、index（只有只读方法）\n\n示例：\n```python\n# 列表\nlst = [1, 2, 3]\nlst.append(4)  # OK\n\n# 元组\ntup = (1, 2, 3)\ntup.append(4)  # AttributeError\n```",
    },
    {
        "title": "什么是Python装饰器？如何使用？",
        "category": "Python编程",
        "difficulty": "medium",
        "description": "解释装饰器的概念和常见应用。",
        "answer": "装饰器（Decorator）：一个接受函数作为参数并返回新函数的高阶函数。\n\n基本语法：\n```python\ndef timer(func):\n    import time\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} 耗时: {time.time()-start:.2f}s')\n        return result\n    return wrapper\n\n@timer\ndef slow_function():\n    import time\n    time.sleep(1)\n```\n\n常见应用：\n1. 日志记录：记录函数调用信息\n2. 性能计时：测量函数执行时间\n3. 权限验证：检查用户权限\n4. 缓存：缓存函数结果（@functools.lru_cache）\n5. 重试机制：失败自动重试\n6. Pytest的@pytest.fixture\n\n带参数的装饰器：\n```python\ndef repeat(n):\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            for _ in range(n):\n                result = func(*args, **kwargs)\n            return result\n        return wrapper\n    return decorator\n\n@repeat(3)\ndef say_hello():\n    print('Hello')\n```",
    },
    {
        "title": "Python中的GIL是什么？对多线程有什么影响？",
        "category": "Python编程",
        "difficulty": "hard",
        "description": "解释GIL的概念和对并发编程的影响。",
        "answer": "GIL（Global Interpreter Lock）：\n- CPython解释器中的全局锁\n- 同一时刻只允许一个线程执行Python字节码\n- 存在原因：简化内存管理，保护引用计数\n\n对多线程的影响：\n1. CPU密集型任务：多线程无法利用多核，可能比单线程更慢\n2. I/O密集型任务：GIL在I/O操作时会释放，多线程仍然有效\n\n解决方案：\n1. 多进程（multiprocessing）：每个进程独立GIL\n2. 异步编程（asyncio）：适合I/O密集型\n3. C扩展：在C代码中释放GIL\n4. 其他解释器：Jython、PyPy（无GIL）\n\n选择建议：\n- CPU密集型：用多进程\n- I/O密集型：用多线程或asyncio\n- 混合型：多进程+异步\n\nPython 3.13+：实验性移除GIL（--disable-gil编译选项）",
    },
    {
        "title": "什么是生成器和迭代器？如何使用？",
        "category": "Python编程",
        "difficulty": "medium",
        "description": "解释生成器和迭代器的概念和区别。",
        "answer": "迭代器（Iterator）：\n- 实现__iter__()和__next__()方法的对象\n- 可以用next()逐个获取元素\n- 耗尽后抛出StopIteration\n\n生成器（Generator）：\n- 使用yield关键字的函数\n- 自动实现迭代器协议\n- 惰性求值，节省内存\n\n示例：\n```python\n# 迭代器\nclass Counter:\n    def __init__(self, max):\n        self.max = max\n        self.current = 0\n    def __iter__(self):\n        return self\n    def __next__(self):\n        if self.current >= self.max:\n            raise StopIteration\n        self.current += 1\n        return self.current\n\n# 生成器\ndef fibonacci():\n    a, b = 0, 1\n    while True:\n        yield a\n        a, b = b, a + b\n\n# 生成器表达式\nsquares = (x**2 for x in range(10))\n```\n\n优势：\n- 内存效率：不需要一次性加载所有数据\n- 延迟计算：按需生成数据\n- 无限序列：可以表示无限数据流",
    },
    {
        "title": "什么是上下文管理器？with语句的工作原理？",
        "category": "Python编程",
        "difficulty": "medium",
        "description": "解释上下文管理器的概念和实现方式。",
        "answer": "上下文管理器：实现__enter__和__exit__方法的对象，用于资源管理。\n\nwith语句工作原理：\n1. 调用__enter__()，返回值赋给as变量\n2. 执行with块中的代码\n3. 无论是否异常，都调用__exit__()清理资源\n\n实现方式：\n```python\n# 方式1：类实现\nclass FileManager:\n    def __init__(self, filename, mode):\n        self.filename = filename\n        self.mode = mode\n    def __enter__(self):\n        self.file = open(self.filename, self.mode)\n        return self.file\n    def __exit__(self, exc_type, exc_val, exc_tb):\n        self.file.close()\n\n# 方式2：contextlib\ntimer:\n    import time\n    @contextmanager\n    def timer():\n        start = time.time()\n        yield\n        print(f'耗时: {time.time()-start:.2f}s')\n\n# 使用\nwith open('file.txt') as f:\n    content = f.read()\n```\n\n常见应用：\n- 文件操作：自动关闭文件\n- 数据库连接：自动释放连接\n- 锁管理：自动释放锁\n- 临时修改环境变量",
    },
]

AUTOMATION_TEST = [
    {
        "title": "什么是Pytest的fixture？如何使用？",
        "category": "自动化测试",
        "difficulty": "medium",
        "description": "解释Pytest fixture的概念和使用方法。",
        "answer": "Fixture是Pytest中用于测试前置准备和清理的机制。\n\n基本使用：\n```python\nimport pytest\n\n@pytest.fixture\ndef login_user():\n    # 前置操作\n    user = {'username': 'test', 'password': '123456'}\n    yield user  # 返回数据给测试\n    # 清理操作\n    print('清理用户数据')\n\ndef test_login(login_user):\n    assert login_user['username'] == 'test'\n```\n\n作用域（scope）：\n- function：每个函数执行一次（默认）\n- class：每个类执行一次\n- module：每个模块执行一次\n- session：整个测试会话执行一次\n\n常用内置fixture：\n- tmp_path：临时目录\n- capsys：捕获输出\n- monkeypatch：修改环境\n- mock：模拟对象\n\nconftest.py共享fixture：\n```python\n# conftest.py\n@pytest.fixture\ndef db_session():\n    session = create_session()\n    yield session\n    session.rollback()\n```\n\n优势：\n- 比setUp/tearDown更灵活\n- 支持依赖注入\n- 可以跨文件共享\n- 支持参数化",
    },
    {
        "title": "什么是POM（Page Object Model）设计模式？",
        "category": "自动化测试",
        "difficulty": "medium",
        "description": "解释POM模式的原理和实现。",
        "answer": "POM（Page Object Model）：将页面元素和操作封装为独立类的设计模式。\n\n核心思想：\n- 每个页面对应一个Page类\n- 封装元素定位（属性）\n- 封装操作方法（行为）\n- 封装断言方法（验证）\n\n实现示例：\n```python\nclass LoginPage:\n    def __init__(self, driver):\n        self.driver = driver\n        self.username_input = (By.ID, 'username')\n        self.password_input = (By.ID, 'password')\n        self.login_button = (By.ID, 'login-btn')\n        self.error_msg = (By.CLASS_NAME, 'error')\n\n    def login(self, username, password):\n        self.driver.find_element(*self.username_input).send_keys(username)\n        self.driver.find_element(*self.password_input).send_keys(password)\n        self.driver.find_element(*self.login_button).click()\n\n    def get_error_message(self):\n        return self.driver.find_element(*self.error_msg).text\n\n    def is_login_success(self):\n        return 'dashboard' in self.driver.current_url\n```\n\n使用：\n```python\ndef test_login_success(driver):\n    login_page = LoginPage(driver)\n    login_page.login('admin', '123456')\n    assert login_page.is_login_success()\n```\n\n优点：\n- 代码复用\n- 易维护（元素变更只改一处）\n- 可读性好\n- 测试用例简洁",
    },
    {
        "title": "Selenium中如何处理动态加载的元素？",
        "category": "自动化测试",
        "difficulty": "medium",
        "description": "说明处理动态元素的等待策略。",
        "answer": "处理动态加载元素的方法：\n\n1. 显式等待（推荐）：\n```python\nfrom selenium.webdriver.support.ui import WebDriverWait\nfrom selenium.webdriver.support import expected_conditions as EC\n\n# 等待元素可见\nelement = WebDriverWait(driver, 10).until(\n    EC.visibility_of_element_located((By.ID, 'dynamic-element'))\n)\n\n# 等待元素可点击\nelement = WebDriverWait(driver, 10).until(\n    EC.element_to_be_clickable((By.ID, 'submit-btn'))\n)\n```\n\n2. 隐式等待：\n```python\ndriver.implicitly_wait(10)  # 全局设置\n```\n\n3. 自定义等待条件：\n```python\ndef wait_for_ajax(driver, timeout=10):\n    WebDriverWait(driver, timeout).until(\n        lambda d: d.execute_script('return jQuery.active == 0')\n    )\n```\n\n4. Fluent Wait（轮询+忽略异常）：\n```python\nwait = WebDriverWait(driver, 10, poll_frequency=0.5,\n                     ignored_exceptions=[NoSuchElementException])\n```\n\n最佳实践：\n- 优先使用显式等待\n- 避免使用time.sleep()\n- 等待时间根据网络环境调整\n- 结合EC条件精确等待",
    },
    {
        "title": "如何设计一个可维护的自动化测试框架？",
        "category": "自动化测试",
        "difficulty": "hard",
        "description": "描述自动化测试框架的架构设计。",
        "answer": "自动化测试框架分层架构：\n\n1. 基础层：\n   - 驱动管理（WebDriver封装）\n   - 配置管理（环境变量、配置文件）\n   - 日志管理\n   - 异常处理\n\n2. 页面对象层：\n   - POM模式封装页面\n   - 公共组件封装\n   - 页面工厂\n\n3. API封装层：\n   - HTTP请求封装\n   - 接口签名\n   - 响应解析\n\n4. 测试数据层：\n   - 数据文件管理（Excel/JSON/YAML）\n   - 数据库操作\n   - 测试数据生成\n\n5. 工具层：\n   - 断言工具\n   - 截图工具\n   - 报告工具\n   - 重试机制\n\n6. 用例层：\n   - 测试用例\n   - 测试套件\n   - 参数化\n\n7. 配置层：\n   - conftest.py\n   - pytest.ini\n   - CI/CD配置\n\n关键原则：\n- 单一职责\n- 数据与脚本分离\n- 支持并行执行\n- 失败自动截图\n- 生成HTML报告",
    },
    {
        "title": "什么是数据驱动测试？如何实现？",
        "category": "自动化测试",
        "difficulty": "medium",
        "description": "解释数据驱动测试的概念和实现方式。",
        "answer": "数据驱动测试（DDT）：测试逻辑与测试数据分离，同一测试用例使用多组数据执行。\n\n实现方式：\n\n1. Pytest参数化：\n```python\n@pytest.mark.parametrize('username,password,expected', [\n    ('admin', '123456', True),\n    ('admin', 'wrong', False),\n    ('', '123456', False),\n])\ndef test_login(username, password, expected):\n    result = login(username, password)\n    assert result == expected\n```\n\n2. 从文件读取：\n```python\nimport json\n\ndef load_test_data(filename):\n    with open(filename) as f:\n        return json.load(f)\n\n@pytest.mark.parametrize('data', load_test_data('test_data.json'))\ndef test_with_file(data):\n    assert login(data['username'], data['password']) == data['expected']\n```\n\n3. pytest-csv：\n```python\n@pytest.mark.parametrize('data', load_csv('test_data.csv'))\ndef test_with_csv(data):\n    pass\n```\n\n优势：\n- 覆盖更多场景\n- 维护成本低（数据变更不改代码）\n- 测试报告更清晰\n- 支持自动生成测试数据",
    },
]

UI_AUTOMATION = [
    {
        "title": "Playwright和Selenium有什么区别？如何选择？",
        "category": "UI自动化",
        "difficulty": "medium",
        "description": "对比Playwright和Selenium的特点。",
        "answer": "Playwright vs Selenium：\n\nPlaywright优势：\n1. 自动等待：元素操作前自动等待可操作\n2. 多浏览器：Chromium、Firefox、WebKit\n3. 请求拦截：可以mock网络请求\n4. 并行执行：原生支持并行\n5. 截图/录屏：内置截图和视频录制\n6. 无头模式：默认无头，速度更快\n7. Codegen：自动生成测试代码\n\nSelenium优势：\n1. 生态成熟：社区大，资料多\n2. 多语言：Java、Python、C#、JS等\n3. Grid：分布式执行\n4. 行业标准：企业级应用广泛\n5. 插件丰富：大量第三方扩展\n\n选择建议：\n- 新项目推荐Playwright\n- 兼容旧系统选Selenium\n- 需要分布式选Selenium Grid\n- 需要API mock选Playwright\n- 团队技术栈决定语言绑定",
    },
    {
        "title": "如何保证自动化测试的稳定性？",
        "category": "UI自动化",
        "difficulty": "hard",
        "description": "解决Flaky Test（不稳定测试）的方法。",
        "answer": "Flaky Test常见原因和解决方案：\n\n1. 元素定位不稳定：\n   - 原因：动态ID、CSS变更\n   - 解决：使用稳定定位策略（data-testid、XPath相对路径）\n\n2. 等待不充分：\n   - 原因：元素未加载就操作\n   - 解决：显式等待替代sleep，等待条件精确\n\n3. 测试数据污染：\n   - 原因：测试间数据依赖\n   - 解决：每次测试前后清理数据，使用独立数据\n\n4. 用例间依赖：\n   - 原因：执行顺序影响结果\n   - 解决：设计独立可运行的用例\n\n5. 环境不稳定：\n   - 原因：网络波动、服务不稳定\n   - 解决：容器化部署，环境隔离\n\n6. 弹窗/对话框干扰：\n   - 原因：未预期的弹窗\n   - 解决：统一处理弹窗，使用try-except\n\n最佳实践：\n- 失败自动截图\n- 重试机制（pytest-rerunfailures）\n- 监控flaky rate\n- 定期清理不稳定用例\n- Docker保证环境一致",
    },
]

# ============================================================
# Stage 5: 测试架构师之路
# ============================================================

TEST_STRATEGY = [
    {
        "title": "什么是BDD和TDD？有什么区别？",
        "category": "测试策略",
        "difficulty": "hard",
        "description": "对比BDD和TDD的概念和实践。",
        "answer": "TDD（测试驱动开发）：\n- 流程：编写失败测试→编写代码通过测试→重构\n- 关注：代码正确性\n- 粒度：函数/方法级别\n- 工具：unittest、pytest、JUnit\n- 参与者：开发人员\n\nBDD（行为驱动开发）：\n- 流程：用自然语言描述行为→实现步骤定义→编写代码\n- 关注：业务正确性\n- 粒度：功能/场景级别\n- 工具：Cucumber、Behave、SpecFlow\n- 参与者：开发+测试+产品\n\nBDD示例（Gherkin语法）：\n```gherkin\nFeature: 用户登录\n  Scenario: 成功登录\n    Given 用户在登录页面\n    When 输入正确的用户名和密码\n    Then 跳转到首页\n    And 显示欢迎信息\n```\n\n区别：\n| 维度 | TDD | BDD |\n|------|-----|-----|\n| 视角 | 技术视角 | 业务视角 |\n| 语言 | 代码 | 自然语言 |\n| 参与者 | 开发 | 全团队 |\n| 粒度 | 单元 | 功能场景 |\n| 工具 | xUnit | Cucumber |",
    },
    {
        "title": "如何测试微服务架构的系统？",
        "category": "测试策略",
        "difficulty": "hard",
        "description": "描述微服务架构下的测试策略。",
        "answer": "微服务测试策略：\n\n测试金字塔：\n1. 单元测试（最多）：测试单个服务的业务逻辑\n2. 契约测试：验证服务间接口契约（Pact）\n3. 集成测试：测试服务间交互\n4. 端到端测试（最少）：测试完整业务流程\n\n契约测试（Contract Testing）：\n- 消费者定义期望（Consumer-Driven Contract）\n- 生成契约文件（Pact文件）\n- 提供者验证契约\n- 优势：不需要完整环境，快速发现接口变更\n\n服务虚拟化：\n- Mock依赖服务\n- 使用WireMock模拟HTTP服务\n- 使用Testcontainers启动真实依赖\n\n混沌工程：\n- 主动注入故障验证系统韧性\n- Chaos Monkey、Litmus\n- 测试超时、重试、熔断机制\n\n监控和可观测性：\n- 分布式链路追踪（Jaeger、Zipkin）\n- 日志聚合（ELK）\n- 指标监控（Prometheus+Grafana）",
    },
    {
        "title": "什么是测试左移？如何在团队中落地？",
        "category": "测试策略",
        "difficulty": "medium",
        "description": "说明测试左移的实践方法。",
        "answer": "测试左移（Shift Left）：将测试活动前移到开发早期阶段。\n\n实践方法：\n\n1. 需求阶段：\n   - 参与需求评审，发现需求缺陷\n   - 编写验收标准（AC）\n   - 使用BDD描述行为\n\n2. 设计阶段：\n   - 参与架构评审\n   - 识别测试风险\n   - 提前设计测试方案\n\n3. 编码阶段：\n   - TDD：测试驱动开发\n   - 代码审查中的测试审查\n   - 单元测试覆盖率要求（>80%）\n   - 静态代码分析（SonarQube）\n\n4. 提交阶段：\n   - Pre-commit Hook\n   - PR自动CI\n   - 代码质量门禁\n\n5. 工具支持：\n   - SonarQube：代码质量扫描\n   - ESLint/Prettier：代码规范\n   - GitHub Actions：PR自动检查\n\n落地策略：\n- 从关键模块开始试点\n- 逐步提高覆盖率要求\n- 建立质量文化",
    },
    {
        "title": "如何设计测试平台？需要哪些核心功能？",
        "category": "测试策略",
        "difficulty": "hard",
        "description": "描述测试平台的架构设计和核心功能。",
        "answer": "测试平台核心功能：\n\n1. 用例管理：\n   - 用例编写、编辑、删除\n   - 用例分类和标签\n   - 用例版本管理\n   - 用例评审流程\n\n2. 执行引擎：\n   - 测试计划编排\n   - 定时执行\n   - 并行执行\n   - 失败重试\n\n3. 报告中心：\n   - 执行结果统计\n   - 趋势分析\n   - 覆盖率报告\n   - 缺陷关联\n\n4. 数据管理：\n   - 测试数据生成\n   - 数据库管理\n   - 环境变量管理\n\n5. 环境管理：\n   - 多环境切换\n   - Docker容器管理\n   - 服务健康检查\n\n6. 缺陷集成：\n   - 对接Jira/禅道\n   - 自动创建缺陷\n   - 缺陷状态同步\n\n7. CI/CD集成：\n   - Jenkins/GitHub Actions\n   - 流水线触发\n   - 质量门禁\n\n技术架构：\n- 前端：Vue3/React\n- 后端：FastAPI/Django\n- 数据库：MySQL/PostgreSQL\n- 缓存：Redis\n- 任务队列：Celery\n- 容器化：Docker+K8s",
    },
]

SECURITY_TEST = [
    {
        "title": "OWASP Top 10有哪些？如何测试？",
        "category": "安全测试",
        "difficulty": "medium",
        "description": "列举OWASP Top 10并说明测试方法。",
        "answer": "OWASP Top 10（2021）：\n\n1. A01 权限控制失效：\n   - 测试：水平/垂直越权访问\n   - 工具：Burp Suite Autorize\n\n2. A02 加密机制失效：\n   - 测试：弱加密、明文传输\n   - 检查：HTTPS配置、密码存储\n\n3. A03 注入攻击：\n   - 测试：SQL注入、NoSQL注入、命令注入\n   - 工具：SQLMap\n\n4. A04 不安全设计：\n   - 测试：业务逻辑漏洞\n   - 方法：威胁建模\n\n5. A05 安全配置错误：\n   - 测试：默认密码、调试模式、目录遍历\n   - 工具：Nmap、Dirb\n\n6. A06 过时组件：\n   - 检查：依赖版本、已知CVE\n   - 工具：OWASP Dependency-Check\n\n7. A07 身份验证失败：\n   - 测试：暴力破解、弱密码、会话管理\n\n8. A08 数据完整性失败：\n   - 测试：反序列化、软件更新验证\n\n9. A09 日志监控失败：\n   - 检查：安全事件是否记录\n\n10. A10 SSRF：\n    - 测试：服务端请求伪造",
    },
    {
        "title": "如何测试越权漏洞？",
        "category": "安全测试",
        "difficulty": "hard",
        "description": "说明水平越权和垂直越权的测试方法。",
        "answer": "越权漏洞类型：\n\n水平越权（同级用户）：\n- 场景：用户A访问用户B的资源\n- 测试方法：\n  1. 修改URL中的ID（/user/1 → /user/2）\n  2. 修改请求体中的用户ID\n  3. 替换Cookie/Token中的用户标识\n  4. 使用用户A的Token请求用户B的数据\n\n垂直越权（不同级别）：\n- 场景：普通用户访问管理员功能\n- 测试方法：\n  1. 用普通Token请求管理员API\n  2. 直接访问管理员页面URL\n  3. 修改角色参数\n\n自动化测试：\n```python\ndef test_horizontal_privity():\n    # 用户A登录\n    token_a = login('user_a', 'password')\n    # 用户B登录\n    token_b = login('user_b', 'password')\n    # 用A的Token访问B的资源\n    response = requests.get('/api/user/2/orders',\n                           headers={'Authorization': f'Bearer {token_a}'})\n    assert response.status_code == 403\n```\n\n防御措施：\n- 服务端校验权限\n- 使用不可预测的ID（UUID）\n- 最小权限原则",
    },
    {
        "title": "什么是XSS攻击？如何测试和防护？",
        "category": "安全测试",
        "difficulty": "medium",
        "description": "解释XSS攻击的类型和防护措施。",
        "answer": "XSS（跨站脚本攻击）：在网页中注入恶意脚本。\n\n类型：\n1. 存储型XSS：\n   - 恶意脚本存储在服务器\n   - 所有访问者都会执行\n   - 场景：评论、论坛、用户资料\n\n2. 反射型XSS：\n   - 恶意脚本在URL中\n   - 用户点击链接时执行\n   - 场景：搜索结果、错误页面\n\n3. DOM型XSS：\n   - 前端JavaScript操作DOM时触发\n   - 不经过服务器\n   - 场景：URL参数直接写入页面\n\n测试方法：\n1. 输入<script>alert(1)</script>\n2. 输入<img src=x onerror=alert(1)>\n3. 输入事件处理器（onload、onerror）\n4. 使用Burp Suite扫描\n5. 手动测试各种标签和事件\n\n防护措施：\n1. 输出编码（HTML、JS、URL编码）\n2. 输入验证和过滤\n3. Content Security Policy（CSP）\n4. HttpOnly Cookie\n5. 使用安全框架（自动转义）",
    },
]

MOBILE_TEST = [
    {
        "title": "Appium和Selenium有什么区别？",
        "category": "移动端测试",
        "difficulty": "medium",
        "description": "对比Appium和Selenium的特点。",
        "answer": "Appium vs Selenium：\n\n相同点：\n- 都基于WebDriver协议\n- 支持多语言（Java、Python、JS等）\n- 使用元素定位+操作模式\n- 支持Page Object Model\n\n不同点：\n| 维度 | Selenium | Appium |\n|------|----------|--------|\n| 测试对象 | Web应用 | 移动应用（Android/iOS） |\n| 底层引擎 | 浏览器驱动 | UIAutomator/XCUITest |\n| 定位方式 | CSS/XPath | Accessibility ID/UIAutomator |\n| 特有操作 | - | 手势（滑动、缩放、长按） |\n| 环境要求 | 浏览器 | SDK/模拟器/真机 |\n| 并行执行 | Selenium Grid | Appium Grid/云测试平台 |\n\nAppium特有功能：\n1. 移动端手势操作\n2. 设备旋转\n3. 应用安装/卸载\n4. 通知栏操作\n5. WebView混合应用测试\n6. TouchAction API",
    },
    {
        "title": "移动端性能测试关注哪些指标？",
        "category": "移动端测试",
        "difficulty": "medium",
        "description": "说明移动端性能测试的关键指标。",
        "answer": "移动端性能测试指标：\n\n1. 启动时间：\n   - 冷启动：首次启动（<2秒）\n   - 热启动：后台恢复（<1秒）\n   - 工具：adb shell am start -W\n\n2. CPU使用率：\n   - 空闲状态：<5%\n   - 正常使用：<30%\n   - 高负载：<70%\n   - 工具：Android Profiler\n\n3. 内存使用：\n   - 内存泄漏检测\n   - 内存抖动（频繁GC）\n   - 工具：LeakCanary、Android Profiler\n\n4. 电量消耗：\n   - 后台耗电\n   - 网络请求频率\n   - 工具：Battery Historian\n\n5. FPS帧率：\n   - 流畅度：>=60fps\n   - 卡顿检测\n   - 工具：PerfDog\n\n6. 网络流量：\n   - 数据消耗\n   - 请求次数\n   - 工具：Charles、Wireshark\n\n7. 包大小：\n   - APK/IPA大小\n   - 资源优化\n\n工具推荐：\n- PerfDog（综合性能测试）\n- Android Profiler（开发调试）\n- Instruments（iOS）",
    },
]

DEVOPS_TEST = [
    {
        "title": "什么是CI/CD？测试在其中的角色？",
        "category": "CI/CD",
        "difficulty": "medium",
        "description": "解释CI/CD的概念和测试融入方式。",
        "answer": "CI（持续集成）：\n- 频繁将代码合并到主干\n- 每次合并自动构建和测试\n- 快速发现集成问题\n\nCD（持续交付/部署）：\n- 持续交付：代码随时可部署到生产\n- 持续部署：通过测试后自动部署\n\n测试在CI/CD中的角色：\n\n1. 提交阶段（秒级）：\n   - 代码规范检查（ESLint）\n   - 单元测试\n   - 静态代码分析\n\n2. 构建阶段（分钟级）：\n   - 编译打包\n   - 接口测试\n   - 集成测试\n\n3. 验收阶段（分钟级）：\n   - UI自动化测试\n   - E2E测试\n   - 性能测试\n\n4. 发布阶段：\n   - 灰度发布验证\n   - 监控告警\n   - 回滚机制\n\n质量门禁：\n- 单元测试覆盖率>80%\n- 0个严重缺陷\n- 代码扫描通过\n- 所有测试通过\n\n工具链：\n- CI：Jenkins、GitHub Actions、GitLab CI\n- 测试：Pytest、Selenium、JMeter\n- 制品：Docker、Nexus\n- 部署：K8s、Ansible",
    },
    {
        "title": "如何用Docker搭建测试环境？",
        "category": "CI/CD",
        "difficulty": "medium",
        "description": "说明使用Docker搭建测试环境的方法。",
        "answer": "Docker搭建测试环境：\n\ndocker-compose.yml示例：\n```yaml\nversion: '3'\nservices:\n  app:\n    build: .\n    ports:\n      - '8080:8080'\n    environment:\n      - DB_HOST=postgres\n      - REDIS_HOST=redis\n    depends_on:\n      - postgres\n      - redis\n\n  postgres:\n    image: postgres:14\n    environment:\n      POSTGRES_DB: testdb\n      POSTGRES_PASSWORD: test123\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n\n  redis:\n    image: redis:7-alpine\n    ports:\n      - '6379:6379'\n\n  selenium:\n    image: selenium/standalone-chrome\n    ports:\n      - '4444:4444'\n\nvolumes:\n  pgdata:\n```\n\n优势：\n- 环境一致性\n- 快速部署（docker-compose up -d）\n- 资源隔离\n- 易于版本管理\n- 支持并行测试\n\n最佳实践：\n- 使用.dockerignore减少镜像大小\n- 多阶段构建优化镜像\n- 使用volume持久化数据\n- 使用network隔离服务",
    },
]

TEST_MANAGEMENT = [
    {
        "title": "如何评估测试覆盖率？",
        "category": "测试管理",
        "difficulty": "medium",
        "description": "说明测试覆盖率的类型和评估方法。",
        "answer": "测试覆盖率类型：\n\n1. 需求覆盖率：\n   - 已测试需求数/总需求数\n   - 工具：需求追踪矩阵\n   - 目标：100%\n\n2. 用例覆盖率：\n   - 已执行用例数/总用例数\n   - 关注通过率\n\n3. 代码覆盖率：\n   - 语句覆盖：执行过的语句比例\n   - 分支覆盖：执行过的分支比例\n   - 路径覆盖：执行过的路径比例\n   - 工具：coverage.py（Python）、JaCoCo（Java）\n\n4. 功能覆盖率：\n   - 已测试功能点/总功能点\n\n评估方法：\n1. 需求追踪矩阵\n2. 代码覆盖率报告\n3. 代码审查\n4. 变异测试（评估测试有效性）\n\n注意事项：\n- 100%覆盖率≠100%质量\n- 覆盖率是必要条件，不是充分条件\n- 关注关键路径和高风险模块\n- 平衡覆盖率和测试成本",
    },
    {
        "title": "敏捷开发中如何做测试？",
        "category": "测试管理",
        "difficulty": "medium",
        "description": "说明敏捷测试的特点和实践。",
        "answer": "敏捷测试特点：\n1. 持续测试：测试贯穿整个Sprint\n2. 快速反馈：尽早发现问题\n3. 全员质量：整个团队对质量负责\n4. 适应变化：灵活应对需求变更\n\n敏捷测试实践：\n\n1. Sprint规划：\n   - 参与故事点估算\n   - 识别测试风险\n   - 规划测试任务\n\n2. 每日站会：\n   - 同步测试进度\n   - 暴露阻塞问题\n\n3. 持续集成：\n   - 自动化测试作为质量门禁\n   - 每次提交触发测试\n\n4. 探索性测试：\n   - 基于Session的测试\n   - 时间盒限制\n   - 发现自动化遗漏的问题\n\n5. 回顾会议：\n   - 分析缺陷根因\n   - 改进测试流程\n\n敏捷测试四象限：\nQ1：技术+支持团队（单元测试、组件测试）\nQ2：业务+支持团队（功能测试、原型验证）\nQ3：业务+评价产品（探索性测试、用户验收）\nQ4：技术+评价产品（性能测试、安全测试）",
    },
]

AI_TEST = [
    {
        "title": "AI在软件测试中有哪些应用？",
        "category": "AI测试",
        "difficulty": "medium",
        "description": "探讨AI在测试领域的应用前景。",
        "answer": "AI在测试中的应用方向：\n\n1. 智能测试用例生成：\n   - 根据需求自动生成测试用例\n   - 基于历史数据优化用例\n   - 工具：Testim、Mabl\n\n2. 视觉回归测试：\n   - AI对比UI截图\n   - 识别视觉差异\n   - 工具：Applitools、Percy\n\n3. 缺陷预测：\n   - 根据代码变更预测高风险区域\n   - 基于历史缺陷数据建模\n   - 优先测试高风险模块\n\n4. 智能测试编排：\n   - 优化测试执行顺序\n   - 根据变更影响选择测试\n   - 减少测试执行时间\n\n5. 自愈测试：\n   - 元素定位失败时自动修复\n   - AI推荐新的定位策略\n   - 减少维护成本\n\n6. 日志分析：\n   - 自动识别异常模式\n   - 根因分析\n   - 智能告警\n\n7. 测试报告自动生成：\n   - AI总结测试结果\n   - 自动生成测试报告\n\n局限性：\n- 不能完全替代人工测试\n- 需要大量训练数据\n- 业务理解有限\n- 创造性测试仍需人工",
    },
]


# ============================================================
# 所有题目集合
# ============================================================

ALL_QUESTIONS = TEST_BASICS + TEST_CASE_DESIGN + DEFECT_MANAGEMENT + COMPUTER_BASICS + \
    FUNCTIONAL_TEST + WEB_TEST + API_TEST + LINUX_TEST + DATABASE_TEST + PERFORMANCE_TEST + \
    PYTHON_PROGRAMMING + AUTOMATION_TEST + UI_AUTOMATION + TEST_STRATEGY + SECURITY_TEST + \
    MOBILE_TEST + DEVOPS_TEST + TEST_MANAGEMENT + AI_TEST


async def seed():
    async with async_session() as session:
        print("=" * 70)
        print("面试题库 V2 种子脚本")
        print("=" * 70)

        # Check existing count
        result = await session.execute(text("SELECT COUNT(*) FROM interview_questions"))
        existing = result.scalar()
        print(f"  现有题目: {existing}")
        print(f"  新增题目: {len(ALL_QUESTIONS)}")

        # Insert new questions
        added = 0
        skipped = 0

        for q in ALL_QUESTIONS:
            # Check for duplicate by title
            result = await session.execute(
                text("SELECT id FROM interview_questions WHERE title = :title"),
                {"title": q["title"]},
            )
            if result.scalar():
                skipped += 1
                continue

            question = InterviewQuestion(
                title=q["title"],
                category=q["category"],
                difficulty=q["difficulty"],
                description=q.get("description", ""),
                answer=q.get("answer", ""),
                content=q.get("content", ""),
                reference_solution=q.get("reference_solution", ""),
                prompt=q.get("prompt", ""),
                test_cases=q.get("test_cases", ""),
                is_published=True,
            )
            session.add(question)
            added += 1

        await session.commit()

        print(f"  新增: {added}")
        print(f"  跳过(重复): {skipped}")

        # Final stats
        result = await session.execute(text("SELECT COUNT(*) FROM interview_questions"))
        final = result.scalar()
        print(f"  总题目数: {final}")

        result = await session.execute(
            text("SELECT category, COUNT(*) FROM interview_questions GROUP BY category ORDER BY COUNT(*) DESC")
        )
        print("\n  按 category 分布:")
        for cat, count in result.fetchall():
            print(f"    {cat}: {count}")

        result = await session.execute(
            text("SELECT difficulty, COUNT(*) FROM interview_questions GROUP BY difficulty ORDER BY COUNT(*) DESC")
        )
        print("\n  按 difficulty 分布:")
        for diff, count in result.fetchall():
            print(f"    {diff}: {count}")

    await engine.dispose()
    print("\n种子数据导入完成！")


if __name__ == "__main__":
    asyncio.run(seed())


