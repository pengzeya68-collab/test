EXERCISES = {
    "缺陷管理与追踪": [
        # ==================== 缺陷生命周期 - 选择题 ====================
        {
            "title": "缺陷生命周期基本概念",
            "description": "缺陷从发现到关闭所经历的状态流转过程称为缺陷生命周期。以下哪个不是缺陷生命周期中的标准状态？\nA. New\nB. Open\nC. Pending\nD. Closed",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "C"
        },
        {
            "title": "缺陷状态流转顺序",
            "description": "在标准缺陷生命周期中，缺陷从新建到关闭的正常流转顺序是？\nA. New -> Open -> Fixed -> Verified -> Closed\nB. New -> Fixed -> Open -> Closed\nC. New -> Closed -> Fixed -> Verified\nD. New -> Verified -> Fixed -> Closed",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "A"
        },
        {
            "title": "缺陷修复后状态",
            "description": "开发人员修复缺陷后，缺陷状态应变更为？\nA. New\nB. Open\nC. Fixed\nD. Closed",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "C"
        },
        {
            "title": "缺陷验证流程",
            "description": "缺陷修复后需要由谁来验证缺陷是否已正确修复？\nA. 开发人员\nB. 测试人员\nC. 产品经理\nD. 项目经理",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "B"
        },
        {
            "title": "缺陷重新打开条件",
            "description": "当测试人员验证缺陷未修复成功时，应该执行什么操作？\nA. 关闭缺陷\nB. 删除缺陷\nC. 创建新缺陷\nD. 重新打开缺陷",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "D"
        },
        {
            "title": "缺陷关闭条件",
            "description": "以下哪种情况可以关闭缺陷？\nA. 测试人员验证修复成功\nB. 开发人员说已修复\nC. 项目经理要求关闭\nD. 缺陷提交超过30天",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "A"
        },
        {
            "title": "缺陷状态图分析",
            "description": "在缺陷生命周期状态图中，以下哪个状态转换是不合理的？\nA. New -> Open\nB. Open -> Fixed\nC. Fixed -> Closed\nD. Closed -> New",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "D"
        },
        {
            "title": "缺陷延期处理",
            "description": "当缺陷被确认存在但决定不在当前版本修复时，应将缺陷状态设为？\nA. New\nB. Open\nC. Deferred\nD. Rejected",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "C"
        },
        {
            "title": "缺陷拒绝处理",
            "description": "开发人员认为缺陷不是真正的问题时，可以将缺陷状态设为？\nA. Fixed\nB. Rejected\nC. Deferred\nD. Closed",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "B"
        },
        {
            "title": "缺陷挂起状态分析",
            "description": "以下哪种情况下缺陷会被置为挂起状态？\nA. 缺陷依赖外部系统修复\nB. 缺陷已修复\nC. 缺陷被拒绝\nD. 缺陷已关闭",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "A"
        },
        # ==================== 缺陷报告编写 - 选择题 ====================
        {
            "title": "缺陷报告基本要素",
            "description": "一份完整的缺陷报告应包含哪些基本要素？\nA. 只需要标题\nB. 只需要截图\nC. 标题、描述、步骤、预期结果、实际结果\nD. 只需要标题和描述",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "C"
        },
        {
            "title": "缺陷标题规范",
            "description": "以下哪个缺陷标题的写法最规范？\nA. 系统有问题\nB. 登录页面输入错误密码后未提示错误信息\nC. Bug\nD. 请修复",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "B"
        },
        {
            "title": "重现步骤编写规范",
            "description": "编写缺陷重现步骤时，以下哪项做法是正确的？\nA. 步骤越简略越好\nB. 每一步都要具体、可操作、可复现\nC. 只写关键步骤\nD. 不需要写步骤",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "B"
        },
        {
            "title": "实际结果与期望结果作用",
            "description": "缺陷报告中实际结果与期望结果的作用是什么？\nA. 美观好看\nB. 帮助开发人员快速理解问题差异\nC. 增加报告长度\nD. 没有实际作用",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "B"
        },
        {
            "title": "缺陷环境信息",
            "description": "缺陷报告中的环境信息不包括以下哪项？\nA. 操作系统版本\nB. 浏览器版本\nC. 开发人员姓名\nD. 应用版本号",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "C"
        },
        {
            "title": "缺陷截图附件作用",
            "description": "在缺陷报告中添加截图的主要目的是什么？\nA. 直观展示问题现象\nB. 增加报告页数\nC. 替代文字描述\nD. 没有必要",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "A"
        },
        {
            "title": "缺陷复现率描述",
            "description": "缺陷复现率为偶现时，应在缺陷报告中如何描述？\nA. 忽略不计\nB. 标注为偶现并记录复现概率\nC. 不提交该缺陷\nD. 标记为必现",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "B"
        },
        {
            "title": "缺陷严重程度描述规范",
            "description": "在缺陷报告中，严重程度字段的作用是？\nA. 让报告看起来更专业\nB. 衡量缺陷对系统的影响程度\nC. 决定开发人员的绩效\nD. 没有实际意义",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "B"
        },
        {
            "title": "缺陷关联需求作用",
            "description": "缺陷报告中关联需求的目的是什么？\nA. 增加工作量\nB. 便于追溯缺陷来源\nC. 让产品经理背锅\nD. 没有必要",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "B"
        },
        {
            "title": "后端接口缺陷报告要素",
            "description": "对于后端接口缺陷，缺陷报告中应优先附带什么信息？\nA. 请求和响应日志\nB. 界面截图\nC. 用户反馈\nD. 设计文档",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "A"
        },
        # ==================== 缺陷分类与优先级 - 选择题 ====================
        {
            "title": "缺陷严重程度等级数量",
            "description": "缺陷严重程度通常分为几个等级？\nA. 2个\nB. 4个\nC. 6个\nD. 8个",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "B"
        },
        {
            "title": "致命缺陷定义",
            "description": "以下哪种缺陷属于致命缺陷？\nA. 系统崩溃导致数据丢失\nB. 界面字体颜色不美观\nC. 某个按钮位置偏移\nD. 日志格式不规范",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "A"
        },
        {
            "title": "严重缺陷示例",
            "description": "以下哪种缺陷属于严重缺陷？\nA. 界面颜色不美观\nB. 某个功能偶尔报错\nC. 核心业务流程中断\nD. 文字拼写错误",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "C"
        },
        {
            "title": "一般缺陷示例",
            "description": "以下哪种缺陷属于一般缺陷？\nA. 系统无法启动\nB. 非核心功能异常\nC. 数据完全丢失\nD. 安全漏洞",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "B"
        },
        {
            "title": "轻微缺陷示例",
            "description": "以下哪种缺陷属于轻微缺陷？\nA. 系统崩溃\nB. 数据错误\nC. 功能缺失\nD. 界面文字对齐问题",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "D"
        },
        {
            "title": "缺陷优先级概念",
            "description": "缺陷优先级表示的是什么？\nA. 缺陷需要被修复的紧急程度\nB. 缺陷的技术难度\nC. 缺陷的影响范围\nD. 缺陷的发现时间",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "A"
        },
        {
            "title": "优先级与严重程度关系",
            "description": "缺陷的优先级和严重程度之间的关系是？\nA. 完全相同\nB. 优先级高的一定严重程度高\nC. 两者独立但可能相关\nD. 完全无关",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "C"
        },
        {
            "title": "缺陷分类维度",
            "description": "缺陷可以从哪些维度进行分类？\nA. 只有严重程度\nB. 严重程度、优先级、类型、来源等多个维度\nC. 只有优先级\nD. 只有类型",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "B"
        },
        {
            "title": "功能缺陷与非功能缺陷区分",
            "description": "以下哪个属于非功能缺陷？\nA. 登录功能失效\nB. 支付金额计算错误\nC. 页面加载超过10秒\nD. 搜索结果不准确",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "C"
        },
        {
            "title": "缺陷来源分类",
            "description": "按缺陷来源分类，以下哪项不属于常见缺陷来源？\nA. 需求阶段\nB. 设计阶段\nC. 市场营销阶段\nD. 编码阶段",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "C"
        },
        # ==================== 缺陷分析方法 - 选择题 ====================
        {
            "title": "缺陷分布分析目的",
            "description": "缺陷分布分析的主要目的是什么？\nA. 识别缺陷集中的模块和区域\nB. 计算缺陷总数\nC. 确定开发人员绩效\nD. 美化报表",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "A"
        },
        {
            "title": "缺陷趋势分析含义",
            "description": "缺陷趋势分析中，发现缺陷数量逐渐下降通常意味着？\nA. 测试不够充分\nB. 产品质量趋于稳定\nC. 开发效率下降\nD. 需求减少",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "B"
        },
        {
            "title": "缺陷根因分析方法",
            "description": "缺陷根因分析常用的分析方法不包括？\nA. 鱼骨图分析\nB. 5个为什么分析\nC. 市场调研\nD. 因果分析法",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "C"
        },
        {
            "title": "缺陷密度计算公式",
            "description": "缺陷密度的计算公式是？\nA. 缺陷数/代码行数\nB. 缺陷数/千行代码数\nC. 缺陷数/模块数\nD. 缺陷数/测试用例数",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "B"
        },
        {
            "title": "缺陷注入阶段分析作用",
            "description": "缺陷注入阶段分析的作用是什么？\nA. 识别缺陷产生的源头阶段\nB. 计算缺陷总数\nC. 确定测试覆盖率\nD. 分配开发任务",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "A"
        },
        {
            "title": "帕累托分析原则",
            "description": "在缺陷分析中，帕累托分析遵循什么原则？\nA. 50/50原则\nB. 80/20原则\nC. 90/10原则\nD. 70/30原则",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "B"
        },
        {
            "title": "缺陷收敛曲线趋势",
            "description": "缺陷收敛曲线的理想趋势是什么？\nA. 新增缺陷逐渐减少，趋于零\nB. 新增缺陷持续增加\nC. 新增缺陷保持不变\nD. 新增缺陷随机波动",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "A"
        },
        {
            "title": "缺陷移除效率计算",
            "description": "缺陷移除效率(DRE)的计算方式是？\nA. 发现缺陷数/总缺陷数\nB. 修复缺陷数/发现缺陷数\nC. 测试阶段发现缺陷数/(测试阶段+发布后发现缺陷数)\nD. 关闭缺陷数/打开缺陷数",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "C"
        },
        {
            "title": "缺陷年龄分析关注点",
            "description": "缺陷年龄分析主要关注什么指标？\nA. 缺陷从发现到关闭的时间\nB. 缺陷的严重程度\nC. 缺陷的优先级\nD. 缺陷的类型",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "A"
        },
        {
            "title": "缺陷聚类分析目的",
            "description": "缺陷聚类分析的目的是什么？\nA. 将缺陷按相似特征分组\nB. 计算缺陷总数\nC. 分配缺陷给开发人员\nD. 关闭所有缺陷",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "A"
        },
        # ==================== 缺陷管理工具 - 选择题 ====================
        {
            "title": "常见缺陷管理工具识别",
            "description": "以下哪个不是常用的缺陷管理工具？\nA. JIRA\nB. Bugzilla\nC. Mantis\nD. Photoshop",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "D"
        },
        {
            "title": "JIRA工作类型",
            "description": "在JIRA中，缺陷通常使用哪种工作类型来跟踪？\nA. Bug\nB. Story\nC. Task\nD. Epic",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "A"
        },
        {
            "title": "缺陷管理工具核心功能",
            "description": "缺陷管理工具的核心功能不包括？\nA. 缺陷跟踪\nB. 状态管理\nC. 代码编写\nD. 报表统计",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "C"
        },
        {
            "title": "缺陷管理工具选型因素",
            "description": "选择缺陷管理工具时，以下哪项不是主要考虑因素？\nA. 团队规模和需求\nB. 工具的易用性\nC. 工具的界面颜色\nD. 与其他工具的集成能力",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "C"
        },
        {
            "title": "Bugzilla工具特点",
            "description": "Bugzilla缺陷管理工具的主要特点是什么？\nA. 开源免费\nB. 只能用于Windows\nC. 不支持Web访问\nD. 只能管理一个项目",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "A"
        },
        {
            "title": "缺陷管理工具与CI/CD集成好处",
            "description": "缺陷管理工具与CI/CD工具集成的主要好处是什么？\nA. 增加工作量\nB. 自动化缺陷创建和状态更新\nC. 让工具更复杂\nD. 没有实际好处",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "B"
        },
        {
            "title": "缺陷工作流配置目的",
            "description": "在缺陷管理工具中配置工作流的目的是什么？\nA. 让界面更美观\nB. 规范缺陷状态流转过程\nC. 增加系统复杂度\nD. 限制用户操作",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "B"
        },
        {
            "title": "缺陷通知机制作用",
            "description": "缺陷管理工具中的通知机制的主要作用是什么？\nA. 骚扰用户\nB. 及时告知相关人员缺陷状态变化\nC. 增加系统负担\nD. 没有实际作用",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "B"
        },
        {
            "title": "缺陷报表功能用途",
            "description": "缺陷管理工具的报表功能主要用于？\nA. 美化数据\nB. 分析缺陷趋势和分布\nC. 增加工作量\nD. 没有实际用途",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "B"
        },
        {
            "title": "缺陷模板配置好处",
            "description": "在缺陷管理工具中配置缺陷模板的好处是？\nA. 增加提交时间\nB. 统一缺陷报告格式，提高效率\nC. 限制用户输入\nD. 让系统更复杂",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "B"
        },
        # ==================== 缺陷预防 - 选择题 ====================
        {
            "title": "缺陷预防核心思想",
            "description": "缺陷预防的核心思想是什么？\nA. 在缺陷产生前采取措施避免缺陷\nB. 等缺陷出现后再修复\nC. 增加测试人员数量\nD. 使用更多工具",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "A"
        },
        {
            "title": "需求阶段预防措施",
            "description": "在需求阶段预防缺陷的有效措施是？\nA. 增加开发人员\nB. 需求评审和原型验证\nC. 延长开发周期\nD. 使用更多测试工具",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "代码审查预防机制",
            "description": "代码审查(Code Review)预防缺陷的主要机制是什么？\nA. 增加代码行数\nB. 通过同行评审发现潜在问题\nC. 延长开发时间\nD. 让代码更复杂",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "缺陷预防成本效益",
            "description": "关于缺陷预防成本，以下说法正确的是？\nA. 预防成本高于后期修复成本\nB. 预防成本通常低于后期修复成本\nC. 预防和修复成本相同\nD. 预防没有成本",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "技术评审预防作用",
            "description": "技术评审在缺陷预防中的作用是什么？\nA. 增加会议时间\nB. 在早期发现设计和架构问题\nC. 让项目更复杂\nD. 没有实际作用",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "编码规范预防作用",
            "description": "制定和执行编码规范对缺陷预防有什么帮助？\nA. 增加代码行数\nB. 减少因编码风格不一致导致的缺陷\nC. 让代码更难读\nD. 没有帮助",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "持续集成预防机制",
            "description": "持续集成(CI)如何帮助预防缺陷？\nA. 增加构建时间\nB. 快速发现集成问题\nC. 让部署更复杂\nD. 没有帮助",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "静态代码分析预防原理",
            "description": "静态代码分析工具预防缺陷的原理是什么？\nA. 在不运行代码的情况下检测潜在问题\nB. 运行代码测试功能\nC. 美化代码格式\nD. 增加代码行数",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "A"
        },
        {
            "title": "结对编程预防优势",
            "description": "结对编程预防缺陷的主要优势是什么？\nA. 增加开发成本\nB. 实时代码审查和知识共享\nC. 延长开发时间\nD. 让代码更复杂",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        {
            "title": "缺陷模式学习方法",
            "description": "通过分析历史缺陷模式来预防缺陷的方法属于？\nA. 随机猜测\nB. 数据驱动的预防策略\nC. 增加测试人员\nD. 延长项目周期",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "B"
        },
        # ==================== 缺陷度量 - 选择题 ====================
        {
            "title": "常用缺陷度量指标",
            "description": "以下哪个是常用的缺陷度量指标？\nA. 代码行数\nB. 开发人员数量\nC. 缺陷密度\nD. 项目预算",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "C"
        },
        {
            "title": "缺陷密度计算示例",
            "description": "如果一个模块有1000行代码，发现了20个缺陷，缺陷密度是多少？\nA. 20个/千行代码\nB. 10个/千行代码\nC. 5个/千行代码\nD. 2个/千行代码",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "A"
        },
        {
            "title": "缺陷平均修复时间含义",
            "description": "缺陷平均修复时间(MTTR)反映的是什么？\nA. 缺陷的严重程度\nB. 团队修复缺陷的效率\nC. 缺陷的数量\nD. 项目的进度",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "B"
        },
        {
            "title": "缺陷reopen率分析",
            "description": "缺陷重新打开率高说明什么问题？\nA. 测试不够严格\nB. 开发人员效率高\nC. 修复质量需要提升\nD. 需求变更频繁",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "C"
        },
        {
            "title": "缺陷检测率计算",
            "description": "缺陷检测率(DDR)的计算公式是？\nA. 测试发现缺陷数/总缺陷数\nB. 开发发现缺陷数/总缺陷数\nC. 测试发现缺陷数/(测试+发布后发现缺陷数)\nD. 关闭缺陷数/打开缺陷数",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "C"
        },
        {
            "title": "缺陷遗留率含义",
            "description": "缺陷遗留率高说明什么？\nA. 测试覆盖率高\nB. 存在较多未解决的缺陷\nC. 开发效率高\nD. 项目进度正常",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "B"
        },
        {
            "title": "缺陷收敛判断标准",
            "description": "如何判断缺陷是否已经收敛？\nA. 新增缺陷数持续低于关闭缺陷数\nB. 缺陷总数不变\nC. 所有缺陷都已关闭\nD. 没有新增缺陷",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "A"
        },
        {
            "title": "缺陷注入阶段统计目的",
            "description": "统计缺陷注入阶段的主要目的是什么？\nA. 增加统计数据\nB. 识别缺陷产生的源头，针对性改进\nC. 让报表更复杂\nD. 没有实际意义",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "B"
        },
        {
            "title": "缺陷严重程度分布分析意义",
            "description": "分析缺陷严重程度分布的意义是什么？\nA. 美化报表\nB. 了解系统质量风险分布\nC. 增加工作量\nD. 没有实际意义",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "B"
        },
        {
            "title": "缺陷模块分布分析作用",
            "description": "分析缺陷在不同模块的分布有助于？\nA. 识别质量薄弱模块，重点改进\nB. 增加模块数量\nC. 让代码更复杂\nD. 没有帮助",
            "instructions": "请选择正确答案",
            "exercise_type": "single_choice",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "A"
        },
        # ==================== 代码题 ====================
        {
            "title": "编写缺陷密度计算函数",
            "description": "编写一个Python函数，计算给定模块的缺陷密度。",
            "instructions": "编写函数 calculate_defect_density(defect_count, loc)，返回缺陷密度（缺陷数/千行代码）",
            "exercise_type": "code",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def calculate_defect_density(defect_count, loc):\n    # 计算缺陷密度 = 缺陷数 / (代码行数 / 1000)\n    pass",
            "solution": "def calculate_defect_density(defect_count, loc):\n    if loc <= 0:\n        return 0\n    return defect_count / (loc / 1000)",
            "test_cases": "[{\"input\": \"calculate_defect_density(20, 1000)\", \"expected\": \"20.0\"}, {\"input\": \"calculate_defect_density(10, 5000)\", \"expected\": \"2.0\"}, {\"input\": \"calculate_defect_density(0, 1000)\", \"expected\": \"0\"}]"
        },
        {
            "title": "编写缺陷状态验证函数",
            "description": "编写一个函数验证缺陷状态流转是否合法。",
            "instructions": "编写函数 is_valid_transition(current_status, new_status)，判断状态转换是否合法",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "code_template": "def is_valid_transition(current_status, new_status):\n    # 合法转换: new->open, open->fixed, fixed->closed, fixed->reopen, open->rejected\n    pass",
            "solution": "def is_valid_transition(current_status, new_status):\n    valid_transitions = {\n        'new': ['open', 'rejected'],\n        'open': ['fixed', 'rejected'],\n        'fixed': ['closed', 'reopen'],\n        'reopen': ['open'],\n        'rejected': ['open'],\n        'closed': []\n    }\n    return new_status in valid_transitions.get(current_status, [])",
            "test_cases": "[{\"input\": \"is_valid_transition('new', 'open')\", \"expected\": \"True\"}, {\"input\": \"is_valid_transition('closed', 'open')\", \"expected\": \"False\"}, {\"input\": \"is_valid_transition('fixed', 'reopen')\", \"expected\": \"True\"}]"
        },
        {
            "title": "编写缺陷分类函数",
            "description": "根据缺陷描述自动判断缺陷严重程度。",
            "instructions": "编写函数 classify_severity(description)，根据关键词返回严重程度",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "code_template": "def classify_severity(description):\n    # 关键词: crash/崩溃->critical, 数据丢失->high, 界面->medium, 文字->low\n    pass",
            "solution": "def classify_severity(description):\n    desc = description.lower()\n    if 'crash' in desc or '崩溃' in desc:\n        return 'critical'\n    elif '数据丢失' in desc or 'data loss' in desc:\n        return 'high'\n    elif '界面' in desc or 'ui' in desc:\n        return 'medium'\n    elif '文字' in desc or 'text' in desc:\n        return 'low'\n    return 'medium'",
            "test_cases": "[{\"input\": \"classify_severity('应用crash了')\", \"expected\": \"critical\"}, {\"input\": \"classify_severity('界面显示异常')\", \"expected\": \"medium\"}, {\"input\": \"classify_severity('文字拼写错误')\", \"expected\": \"low\"}]"
        },
        {
            "title": "编写缺陷趋势分析函数",
            "description": "分析缺陷数量趋势，判断是否收敛。",
            "instructions": "编写函数 is_converging(defect_counts)，判断缺陷趋势是否收敛",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "code_template": "def is_converging(defect_counts):\n    # 连续3个周期缺陷数递减则认为收敛\n    pass",
            "solution": "def is_converging(defect_counts):\n    if len(defect_counts) < 4:\n        return False\n    for i in range(len(defect_counts) - 3):\n        if defect_counts[i] > defect_counts[i+1] > defect_counts[i+2] > defect_counts[i+3]:\n            return True\n    return False",
            "test_cases": "[{\"input\": \"is_converging([10, 8, 6, 4, 2])\", \"expected\": \"True\"}, {\"input\": \"is_converging([10, 8, 9, 7, 5])\", \"expected\": \"False\"}, {\"input\": \"is_converging([10, 9, 8, 7])\", \"expected\": \"True\"}]"
        },
        {
            "title": "编写缺陷修复效率计算",
            "description": "计算缺陷的平均修复时间。",
            "instructions": "编写函数 calculate_mttr(repair_times)，返回平均修复时间",
            "exercise_type": "code",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def calculate_mttr(repair_times):\n    # MTTR = 总修复时间 / 缺陷数量\n    pass",
            "solution": "def calculate_mttr(repair_times):\n    if not repair_times:\n        return 0\n    return sum(repair_times) / len(repair_times)",
            "test_cases": "[{\"input\": \"calculate_mttr([2, 4, 6, 8])\", \"expected\": \"5.0\"}, {\"input\": \"calculate_mttr([10])\", \"expected\": \"10.0\"}, {\"input\": \"calculate_mttr([])\" , \"expected\": \"0\"}]"
        },
        {
            "title": "编写缺陷优先级排序函数",
            "description": "根据严重程度和紧急程度对缺陷进行优先级排序。",
            "instructions": "编写函数 sort_defects(defects)，按优先级排序缺陷列表",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "code_template": "def sort_defects(defects):\n    # defects格式: [{\"id\": 1, \"severity\": \"critical\", \"priority\": \"high\"}]\n    # 优先级排序: severity权重 + priority权重\n    pass",
            "solution": "def sort_defects(defects):\n    severity_weight = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}\n    priority_weight = {'high': 3, 'medium': 2, 'low': 1}\n    def get_score(d):\n        return severity_weight.get(d.get('severity', 'low'), 0) + priority_weight.get(d.get('priority', 'low'), 0)\n    return sorted(defects, key=get_score, reverse=True)",
            "test_cases": "[{\"input\": \"sort_defects([{'id': 1, 'severity': 'low', 'priority': 'low'}, {'id': 2, 'severity': 'critical', 'priority': 'high'}])\", \"expected\": \"[{'id': 2, 'severity': 'critical', 'priority': 'high'}, {'id': 1, 'severity': 'low', 'priority': 'low'}]\"}]"
        },
        {
            "title": "编写缺陷报告生成函数",
            "description": "根据缺陷信息生成标准化的缺陷报告摘要。",
            "instructions": "编写函数 generate_summary(defect)，返回格式化的缺陷摘要字符串",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "code_template": "def generate_summary(defect):\n    # defect: {\"id\": 1, \"title\": \"\", \"severity\": \"\", \"status\": \"\", \"assignee\": \"\"}\n    # 返回格式: [ID] 标题 | 严重程度 | 状态 | 负责人\n    pass",
            "solution": "def generate_summary(defect):\n    return \"[{}] {} | {} | {} | {}\".format(\n        defect.get('id', ''),\n        defect.get('title', ''),\n        defect.get('severity', ''),\n        defect.get('status', ''),\n        defect.get('assignee', '')\n    )",
            "test_cases": "[{\"input\": \"generate_summary({'id': 1, 'title': '登录失败', 'severity': 'high', 'status': 'open', 'assignee': '张三'})\", \"expected\": \"[1] 登录失败 | high | open | 张三\"}]"
        },
        {
            "title": "编写缺陷重复检测函数",
            "description": "检测新提交的缺陷是否与已有缺陷重复。",
            "instructions": "编写函数 is_duplicate(new_defect, existing_defects)，判断是否存在重复缺陷",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "code_template": "def is_duplicate(new_defect, existing_defects):\n    # 根据标题相似度判断是否重复\n    pass",
            "solution": "def is_duplicate(new_defect, existing_defects):\n    new_title = new_defect.get('title', '').lower()\n    for defect in existing_defects:\n        existing_title = defect.get('title', '').lower()\n        if new_title == existing_title:\n            return True\n        new_words = set(new_title.split())\n        existing_words = set(existing_title.split())\n        if new_words and existing_words:\n            overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))\n            if overlap > 0.8:\n                return True\n    return False",
            "test_cases": "[{\"input\": \"is_duplicate({'title': '登录按钮失效'}, [{'title': '登录按钮失效'}, {'title': '注册页面错误'}])\", \"expected\": \"True\"}, {\"input\": \"is_duplicate({'title': '支付功能异常'}, [{'title': '登录按钮失效'}])\", \"expected\": \"False\"}]"
        },
        {
            "title": "编写缺陷统计报表函数",
            "description": "统计各严重程度的缺陷数量。",
            "instructions": "编写函数 count_by_severity(defects)，返回各严重程度缺陷数量的字典",
            "exercise_type": "code",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def count_by_severity(defects):\n    # 统计 critical, high, medium, low 各级别数量\n    pass",
            "solution": "def count_by_severity(defects):\n    result = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}\n    for defect in defects:\n        severity = defect.get('severity', 'medium')\n        if severity in result:\n            result[severity] += 1\n    return result",
            "test_cases": "[{\"input\": \"count_by_severity([{'severity': 'critical'}, {'severity': 'high'}, {'severity': 'low'}])\", \"expected\": \"{'critical': 1, 'high': 1, 'medium': 0, 'low': 1}\"}]"
        },
        {
            "title": "编写缺陷关闭率计算函数",
            "description": "计算已关闭缺陷占总缺陷的比例。",
            "instructions": "编写函数 calculate_close_rate(defects)，返回关闭率百分比",
            "exercise_type": "code",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def calculate_close_rate(defects):\n    # 关闭率 = 已关闭缺陷数 / 总缺陷数 * 100\n    pass",
            "solution": "def calculate_close_rate(defects):\n    if not defects:\n        return 0\n    closed_count = sum(1 for d in defects if d.get('status') == 'closed')\n    return round(closed_count / len(defects) * 100, 2)",
            "test_cases": "[{\"input\": \"calculate_close_rate([{'status': 'closed'}, {'status': 'open'}, {'status': 'closed'}])\", \"expected\": \"66.67\"}, {\"input\": \"calculate_close_rate([])\", \"expected\": \"0\"}]"
        },
        {
            "title": "编写缺陷模块分布函数",
            "description": "统计缺陷在各模块的分布情况。",
            "instructions": "编写函数 count_by_module(defects)，返回各模块缺陷数量",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "code_template": "def count_by_module(defects):\n    # 统计各模块缺陷数量\n    pass",
            "solution": "def count_by_module(defects):\n    result = {}\n    for defect in defects:\n        module = defect.get('module', 'unknown')\n        result[module] = result.get(module, 0) + 1\n    return result",
            "test_cases": "[{\"input\": \"count_by_module([{'module': 'login'}, {'module': 'login'}, {'module': 'payment'}])\", \"expected\": \"{'login': 2, 'payment': 1}\"}]"
        },
        {
            "title": "编写缺陷年龄计算函数",
            "description": "计算缺陷从创建到当前的存活天数。",
            "instructions": "编写函数 calculate_defect_age(create_date, current_date)，返回天数差",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "from datetime import datetime\n\ndef calculate_defect_age(create_date, current_date):\n    # 日期格式: 'YYYY-MM-DD'\n    # 返回天数差\n    pass",
            "solution": "from datetime import datetime\n\ndef calculate_defect_age(create_date, current_date):\n    fmt = '%Y-%m-%d'\n    d1 = datetime.strptime(create_date, fmt)\n    d2 = datetime.strptime(current_date, fmt)\n    return (d2 - d1).days",
            "test_cases": "[{\"input\": \"calculate_defect_age('2024-01-01', '2024-01-10')\", \"expected\": \"9\"}, {\"input\": \"calculate_defect_age('2024-01-01', '2024-01-01')\", \"expected\": \"0\"}]"
        },
        {
            "title": "编写缺陷修复及时率函数",
            "description": "计算在SLA时限内修复的缺陷比例。",
            "instructions": "编写函数 calculate_sla_compliance(defects, sla_days)，返回SLA达标率",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def calculate_sla_compliance(defects, sla_days):\n    # defects: [{\"fix_days\": 3}, {\"fix_days\": 7}]\n    # SLA达标率 = 修复天数<=sla_days的缺陷数 / 已修复缺陷数\n    pass",
            "solution": "def calculate_sla_compliance(defects, sla_days):\n    fixed = [d for d in defects if d.get('fix_days') is not None]\n    if not fixed:\n        return 0\n    compliant = sum(1 for d in fixed if d['fix_days'] <= sla_days)\n    return round(compliant / len(fixed) * 100, 2)",
            "test_cases": "[{\"input\": \"calculate_sla_compliance([{'fix_days': 2}, {'fix_days': 5}, {'fix_days': 10}], 7)\", \"expected\": \"66.67\"}]"
        },
        {
            "title": "编写缺陷阶段分布分析函数",
            "description": "分析缺陷在不同开发阶段的分布情况。",
            "instructions": "编写函数 analyze_phase_distribution(defects)，返回各阶段缺陷占比",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "code_template": "def analyze_phase_distribution(defects):\n    # defects: [{\"phase\": \"requirement\"}, {\"phase\": \"design\"}]\n    # 返回各阶段占比字典\n    pass",
            "solution": "def analyze_phase_distribution(defects):\n    if not defects:\n        return {}\n    phase_count = {}\n    for d in defects:\n        phase = d.get('phase', 'unknown')\n        phase_count[phase] = phase_count.get(phase, 0) + 1\n    total = len(defects)\n    return {phase: round(count / total * 100, 2) for phase, count in phase_count.items()}",
            "test_cases": "[{\"input\": \"analyze_phase_distribution([{'phase': 'coding'}, {'phase': 'coding'}, {'phase': 'requirement'}])\", \"expected\": \"{'coding': 66.67, 'requirement': 33.33}\"}]"
        },
        {
            "title": "编写缺陷预测函数",
            "description": "根据历史缺陷数据预测下一阶段缺陷数量。",
            "instructions": "编写函数 predict_defects(history, period)，使用简单移动平均预测",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "code_template": "def predict_defects(history, period):\n    # 使用最近period个数据的平均值预测\n    pass",
            "solution": "def predict_defects(history, period):\n    if not history or period <= 0:\n        return 0\n    recent = history[-period:]\n    return round(sum(recent) / len(recent), 2)",
            "test_cases": "[{\"input\": \"predict_defects([10, 8, 6, 4, 2], 3)\", \"expected\": \"4.0\"}, {\"input\": \"predict_defects([5, 3], 3)\", \"expected\": \"4.0\"}]"
        },
        {
            "title": "编写缺陷标签统计函数",
            "description": "统计缺陷标签出现频率并排序。",
            "instructions": "编写函数 count_tags(defects)，返回标签频率字典按频率降序排列",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "code_template": "def count_tags(defects):\n    # defects: [{\"tags\": [\"UI\", \"性能\"]}]\n    # 统计各标签出现次数\n    pass",
            "solution": "def count_tags(defects):\n    tag_count = {}\n    for d in defects:\n        for tag in d.get('tags', []):\n            tag_count[tag] = tag_count.get(tag, 0) + 1\n    return dict(sorted(tag_count.items(), key=lambda x: x[1], reverse=True))",
            "test_cases": "[{\"input\": \"count_tags([{'tags': ['UI', '性能']}, {'tags': ['UI', '安全']}, {'tags': ['性能']}])\", \"expected\": \"{'UI': 2, '性能': 2, '安全': 1}\"}]"
        },
        {
            "title": "编写缺陷责任分配函数",
            "description": "根据模块自动分配缺陷给对应负责人。",
            "instructions": "编写函数 assign_defect(defect, module_owners)，返回负责人",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "code_template": "def assign_defect(defect, module_owners):\n    # module_owners: {\"login\": \"张三\", \"payment\": \"李四\"}\n    # 根据缺陷模块分配负责人\n    pass",
            "solution": "def assign_defect(defect, module_owners):\n    module = defect.get('module', '')\n    return module_owners.get(module, '未分配')",
            "test_cases": "[{\"input\": \"assign_defect({'module': 'login'}, {'login': '张三', 'payment': '李四'})\", \"expected\": \"张三\"}, {\"input\": \"assign_defect({'module': 'test'}, {'login': '张三'})\", \"expected\": \"未分配\"}]"
        },
        {
            "title": "编写缺陷过滤函数",
            "description": "根据多个条件过滤缺陷列表。",
            "instructions": "编写函数 filter_defects(defects, criteria)，返回符合条件的缺陷",
            "exercise_type": "code",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "code_template": "def filter_defects(defects, criteria):\n    # criteria: {\"severity\": \"critical\", \"status\": \"open\"}\n    # 返回满足所有条件的缺陷\n    pass",
            "solution": "def filter_defects(defects, criteria):\n    result = []\n    for d in defects:\n        match = True\n        for key, value in criteria.items():\n            if d.get(key) != value:\n                match = False\n                break\n        if match:\n            result.append(d)\n    return result",
            "test_cases": "[{\"input\": \"filter_defects([{'severity': 'critical', 'status': 'open'}, {'severity': 'low', 'status': 'open'}], {'severity': 'critical'})\", \"expected\": \"[{'severity': 'critical', 'status': 'open'}]\"}]"
        },
        {
            "title": "编写缺陷解决时间统计函数",
            "description": "统计不同严重程度缺陷的平均解决时间。",
            "instructions": "编写函数 avg_fix_time_by_severity(defects)，返回各严重程度平均修复时间",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def avg_fix_time_by_severity(defects):\n    # defects: [{\"severity\": \"critical\", \"fix_days\": 2}]\n    # 返回各严重程度的平均修复时间\n    pass",
            "solution": "def avg_fix_time_by_severity(defects):\n    severity_times = {}\n    for d in defects:\n        sev = d.get('severity', 'unknown')\n        fix_days = d.get('fix_days')\n        if fix_days is not None:\n            if sev not in severity_times:\n                severity_times[sev] = []\n            severity_times[sev].append(fix_days)\n    return {sev: round(sum(times) / len(times), 2) for sev, times in severity_times.items() if times}",
            "test_cases": "[{\"input\": \"avg_fix_time_by_severity([{'severity': 'critical', 'fix_days': 1}, {'severity': 'critical', 'fix_days': 3}, {'severity': 'low', 'fix_days': 10}])\", \"expected\": \"{'critical': 2.0, 'low': 10.0}\"}]"
        },
        {
            "title": "编写缺陷逃逸率计算函数",
            "description": "计算缺陷逃逸到生产环境的比率。",
            "instructions": "编写函数 calculate_escape_rate(defects)，返回逃逸率",
            "exercise_type": "code",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "code_template": "def calculate_escape_rate(defects):\n    # defects: [{\"found_in\": \"testing\"}, {\"found_in\": \"production\"}]\n    # 逃逸率 = 生产环境发现的缺陷 / 总缺陷数\n    pass",
            "solution": "def calculate_escape_rate(defects):\n    if not defects:\n        return 0\n    production_count = sum(1 for d in defects if d.get('found_in') == 'production')\n    return round(production_count / len(defects) * 100, 2)",
            "test_cases": "[{\"input\": \"calculate_escape_rate([{'found_in': 'testing'}, {'found_in': 'testing'}, {'found_in': 'production'}])\", \"expected\": \"33.33\"}]"
        },
        # ==================== 文本题 ====================
        {
            "title": "描述缺陷生命周期各状态",
            "description": "请描述缺陷生命周期中各个状态的含义。",
            "instructions": "请详细描述新建、打开、已修复、已关闭、重新打开、拒绝等状态的含义",
            "exercise_type": "text",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "新建(New)：缺陷刚被发现并提交；打开(Open)：缺陷已被确认并分配给开发人员；已修复(Fixed)：开发人员已完成修复；已关闭(Closed)：测试人员验证修复成功；重新打开(Reopen)：验证发现未修复成功；已拒绝(Rejected)：开发人员认为不是缺陷"
        },
        {
            "title": "说明缺陷报告的作用",
            "description": "请说明一份好的缺陷报告对软件开发团队的作用。",
            "instructions": "从沟通效率、问题定位、质量改进等角度分析缺陷报告的重要性",
            "exercise_type": "text",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "好的缺陷报告能提高沟通效率，帮助开发人员快速定位问题，减少反复沟通；为质量改进提供数据支持；帮助团队积累经验教训；促进测试与开发的协作"
        },
        {
            "title": "解释缺陷严重程度与优先级的区别",
            "description": "请解释缺陷严重程度和优先级这两个概念的区别与联系。",
            "instructions": "详细说明两者的定义、区别以及在实际工作中如何综合考虑",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "严重程度衡量缺陷对系统的影响程度，是客观的技术指标；优先级衡量修复缺陷的紧迫程度，受业务影响、发布计划等主观因素影响。严重程度高的缺陷优先级不一定高，例如界面错别字严重程度低但面向客户时优先级可能高"
        },
        {
            "title": "描述缺陷根因分析方法",
            "description": "请描述常用的缺陷根因分析方法及其适用场景。",
            "instructions": "至少描述三种根因分析方法，说明其原理和适用场景",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "1.鱼骨图分析：从人、机、料、法、环五个维度分析缺陷原因；2.5个为什么分析法：连续追问为什么直到找到根本原因；3.因果分析法：分析缺陷产生的直接原因和根本原因；4.帕累托分析：找出导致80%缺陷的20%原因"
        },
        {
            "title": "说明如何选择缺陷管理工具",
            "description": "请说明选择缺陷管理工具时应考虑哪些因素。",
            "instructions": "从团队规模、项目需求、集成能力、成本等方面分析选型要点",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "选型考虑因素：1.团队规模和使用习惯；2.项目管理需求（工作流定制）；3.与其他工具的集成能力；4.报表和数据分析功能；5.成本和部署方式；6.易用性和学习成本；7.技术支持和社区活跃度"
        },
        {
            "title": "描述缺陷预防策略",
            "description": "请描述在软件开发生命周期各阶段可以采取的缺陷预防措施。",
            "instructions": "分别说明需求、设计、编码、测试阶段的缺陷预防措施",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "需求阶段：需求评审、原型验证；设计阶段：设计评审、架构验证；编码阶段：代码审查、编码规范、单元测试、静态分析；测试阶段：测试用例评审、自动化测试、持续集成"
        },
        {
            "title": "分析缺陷密度指标的意义",
            "description": "请分析缺陷密度指标在质量管理中的作用和局限性。",
            "instructions": "说明缺陷密度的计算方法、应用场景和局限性",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "缺陷密度=缺陷数/代码行数(KLOC)，用于评估代码质量、比较模块质量、预测测试重点。局限性：不同语言代码行数不可比；受测试充分程度影响；无法反映缺陷严重程度；新旧代码密度差异大"
        },
        {
            "title": "描述缺陷分类标准",
            "description": "请描述如何制定缺陷分类标准，使其适用于团队的实际情况。",
            "instructions": "说明制定分类标准的步骤、考虑因素和实施要点",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "步骤：1.调研行业标准和最佳实践；2.分析团队历史缺陷数据；3.与开发、测试、产品共同讨论；4.定义分类维度和等级；5.编写分类标准文档；6.培训和试运行；7.定期回顾和优化"
        },
        {
            "title": "说明缺陷趋势分析的作用",
            "description": "请说明缺陷趋势分析在项目管理中的作用。",
            "instructions": "分析缺陷趋势如何帮助项目决策和质量评估",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "缺陷趋势分析可帮助：1.评估项目质量状况；2.预测发布时间；3.识别质量风险；4.评估测试充分性；5.指导资源分配；6.为过程改进提供依据"
        },
        {
            "title": "描述缺陷管理工作流设计",
            "description": "请描述如何设计适合团队的缺陷管理工作流。",
            "instructions": "说明工作流设计的原则、关键节点和注意事项",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "设计原则：简洁高效、职责清晰、可追溯。关键节点：提交、分配、修复、验证、关闭。注意事项：状态不宜过多；明确每个状态的负责人；设置超时提醒；支持批量操作；与开发流程集成"
        },
        {
            "title": "说明代码审查对缺陷预防的作用",
            "description": "请详细说明代码审查如何帮助预防缺陷。",
            "instructions": "从知识共享、规范执行、早期发现等角度分析代码审查的价值",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "代码审查预防缺陷的机制：1.多双眼睛检查，发现作者遗漏的问题；2.促进编码规范执行；3.知识共享，减少因不熟悉代码导致的缺陷；4.早期发现设计和逻辑问题；5.培养团队质量意识；6.建立代码质量基准"
        },
        {
            "title": "分析缺陷逃逸的影响",
            "description": "请分析缺陷逃逸到生产环境的影响和应对措施。",
            "instructions": "说明缺陷逃逸的成本影响、质量影响和预防措施",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "影响：1.修复成本成倍增加；2.影响用户体验和满意度；3.可能造成经济损失；4.影响团队信誉。预防措施：1.完善测试策略；2.加强代码审查；3.引入自动化测试；4.建立质量门禁；5.分析逃逸原因并改进"
        },
        {
            "title": "描述缺陷管理流程优化方法",
            "description": "请描述如何持续优化缺陷管理流程。",
            "instructions": "从度量分析、工具改进、团队协作等方面说明优化方法",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "优化方法：1.定期度量分析，找出瓶颈；2.收集团队反馈，识别痛点；3.简化不必要的流程步骤；4.引入自动化工具；5.建立缺陷管理规范；6.定期培训和知识分享；7.与业界最佳实践对标"
        },
        {
            "title": "说明如何处理争议缺陷",
            "description": "请说明当开发和测试对缺陷存在争议时的处理方法。",
            "instructions": "描述争议处理的原则、流程和沟通技巧",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "处理原则：基于事实和数据，对事不对人。流程：1.双方陈述理由；2.查阅需求文档和设计规范；3.参考行业标准和最佳实践；4.必要时请产品经理或技术负责人仲裁；5.记录决策结果和理由；6.更新缺陷分类标准"
        },
        {
            "title": "描述缺陷管理在敏捷开发中的应用",
            "description": "请描述敏捷开发环境下缺陷管理的特点和实践。",
            "instructions": "说明敏捷开发中缺陷管理与传统方式的区别",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "敏捷环境特点：1.缺陷作为用户故事管理；2.在Sprint内快速修复；3.每日站会同步缺陷状态；4.回顾会分析缺陷根因；5.使用看板可视化缺陷状态；6.强调自动化测试预防缺陷；7.轻量级文档，注重沟通"
        },
        {
            "title": "说明缺陷度量指标体系设计",
            "description": "请描述如何设计全面的缺陷度量指标体系。",
            "instructions": "说明指标选择、数据收集、分析应用等方面",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "指标体系设计：1.过程指标：缺陷发现率、修复率、关闭率；2.效率指标：平均修复时间、SLA达标率；3.质量指标：缺陷密度、逃逸率、reopen率；4.分布指标：模块分布、严重程度分布、注入阶段分布。需配套数据收集工具和定期分析报告"
        },
        {
            "title": "描述缺陷预防的成本效益分析",
            "description": "请分析缺陷预防投入与收益之间的关系。",
            "instructions": "说明缺陷预防的成本构成、收益体现和投资回报",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "成本构成：培训投入、工具采购、流程改进、审查时间。收益体现：减少后期修复成本（需求阶段修复成本是生产环境的1/100）；提高产品质量；减少客户投诉；提升团队效率。投资回报：预防投入通常能带来3-10倍的成本节约"
        },
        {
            "title": "说明缺陷管理与质量管理的关系",
            "description": "请阐述缺陷管理在质量管理体系中的地位和作用。",
            "instructions": "说明缺陷管理如何支撑质量管理目标的实现",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "缺陷管理是质量管理的核心组成部分：1.提供质量度量数据；2.识别质量改进机会；3.验证质量改进效果；4.支撑质量决策；5.促进质量文化建设。通过缺陷管理实现质量的度量、分析、改进和控制"
        },
        {
            "title": "描述缺陷管理中的沟通技巧",
            "description": "请描述在缺陷管理过程中如何进行有效沟通。",
            "instructions": "说明与开发人员、产品经理、管理层等不同角色的沟通要点",
            "exercise_type": "text",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "沟通技巧：1.对开发：提供清晰的重现步骤和证据，避免指责性语言；2.对产品：说明缺陷的业务影响和优先级依据；3.对管理层：提供数据支撑的质量报告；4.通用原则：基于事实、对事不对人、及时沟通、记录决策"
        },
        {
            "title": "说明如何建立缺陷管理规范",
            "description": "请描述如何为团队建立统一的缺陷管理规范。",
            "instructions": "说明规范的内容、制定流程和推广方法",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "规范内容：1.缺陷提交模板和必填字段；2.严重程度和优先级定义；3.状态流转规则；4.响应时间要求；5.定期评审机制。制定流程：调研现状、起草规范、团队评审、试行完善、正式发布。推广方法：培训、示范、检查、反馈"
        },
        {
            "title": "描述缺陷管理在DevOps中的应用",
            "description": "请描述DevOps环境下缺陷管理的实践方法。",
            "instructions": "说明如何将缺陷管理融入DevOps工具链和流程",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "DevOps实践：1.缺陷自动创建（监控告警触发）；2.与CI/CD流水线集成；3.自动分配和通知；4.与日志、监控系统关联；5.自动验证修复；6.闭环反馈机制。优势：缩短发现-修复周期，提高响应速度"
        },
        {
            "title": "说明缺陷管理在微服务架构中的挑战",
            "description": "请分析微服务架构下缺陷管理面临的挑战和应对策略。",
            "instructions": "说明分布式系统缺陷定位、跨服务协调等挑战",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "挑战：1.缺陷定位困难（分布式调用链）；2.跨服务协调复杂；3.环境一致性问题；4.版本管理复杂。应对策略：1.分布式链路追踪；2.统一日志平台；3.服务依赖可视化；4.容器化环境管理；5.跨团队协作机制"
        },
        {
            "title": "描述缺陷管理中的数据安全",
            "description": "请说明在缺陷管理过程中如何保障数据安全。",
            "instructions": "说明缺陷数据的敏感性、保护措施和合规要求",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷管理工具",
            "solution": "数据安全措施：1.访问权限控制（按角色授权）；2.敏感信息脱敏（生产数据）；3.审计日志记录；4.数据加密存储；5.定期安全审查；6.合规性检查（GDPR等）；7.备份和恢复机制"
        },
        {
            "title": "说明如何处理历史遗留缺陷",
            "description": "请描述如何有效管理和处理历史遗留缺陷。",
            "instructions": "说明遗留缺陷的评估、分类和处理策略",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "处理策略：1.全面梳理和评估；2.按影响和成本分类；3.制定清理计划；4.优先处理高影响缺陷；5.关闭过时缺陷；6.建立防止新增遗留的机制；7.定期回顾和跟踪进度"
        },
        {
            "title": "描述缺陷管理中的自动化实践",
            "description": "请描述缺陷管理中可以应用自动化的场景。",
            "instructions": "说明自动化在缺陷发现、分类、跟踪等环节的应用",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "自动化场景：1.自动缺陷发现（监控、自动化测试）；2.自动分类（机器学习）；3.自动分配（基于模块和人员）；4.自动通知和提醒；5.自动验证（回归测试）；6.自动生成报告；7.自动关闭过期缺陷"
        },
        {
            "title": "说明缺陷管理在不同开发模型中的差异",
            "description": "请对比缺陷管理在瀑布模型和敏捷模型中的差异。",
            "instructions": "从流程、工具、度量等方面对比两种模型的差异",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷生命周期",
            "solution": "瀑布模型：流程严格、文档完整、缺陷集中管理、阶段明确。敏捷模型：流程灵活、轻量文档、与用户故事融合、快速迭代。差异：敏捷强调内建质量，缺陷预防优于发现；瀑布强调阶段评审，缺陷集中处理"
        },
        {
            "title": "描述缺陷管理培训计划",
            "description": "请描述如何为新员工制定缺陷管理培训计划。",
            "instructions": "说明培训内容、方式和评估方法",
            "exercise_type": "text",
            "difficulty": "easy",
            "category": "缺陷管理",
            "knowledge_point": "缺陷报告编写",
            "solution": "培训计划：1.理论知识：缺陷管理概念、流程、工具；2.实操练习：提交缺陷、状态流转、报告生成；3.案例分析：优秀和问题缺陷报告对比；4.考核评估：提交测试缺陷、参与评审。培训方式：讲解+实操+导师指导"
        },
        {
            "title": "说明缺陷管理与项目风险的关系",
            "description": "请分析缺陷管理如何帮助识别和控制项目风险。",
            "instructions": "说明缺陷数据如何反映项目风险状况",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分析方法",
            "solution": "风险识别：1.缺陷趋势异常反映质量风险；2.缺陷集中模块反映技术债务；3.修复周期延长反映资源风险；4.缺陷reopen率高反映流程风险。风险控制：1.设置质量门禁；2.建立预警机制；3.制定应对预案；4.定期风险评审"
        },
        {
            "title": "描述缺陷管理的持续改进方法",
            "description": "请描述如何持续改进缺陷管理实践。",
            "instructions": "说明改进的驱动因素、方法和评估机制",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷预防",
            "solution": "驱动因素：度量数据分析、团队反馈、行业对标。改进方法：1.定期回顾会分析问题；2.制定改进计划并跟踪；3.引入新工具和技术；4.优化流程和规范；5.加强培训和知识分享。评估机制：改进前后指标对比、团队满意度调查"
        },
        {
            "title": "说明缺陷管理在质量管理认证中的作用",
            "description": "请说明缺陷管理如何支撑ISO/CMMI等质量认证。",
            "instructions": "说明缺陷管理在质量认证中的要求和实践",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷度量",
            "solution": "认证要求：1.缺陷管理流程定义；2.缺陷记录完整性；3.缺陷度量和分析；4.缺陷预防措施；5.持续改进机制。实践要点：1.建立文档化流程；2.保留完整记录；3.定期度量分析；4.证明改进效果；5.培训和意识提升"
        },
        {
            "title": "描述移动应用缺陷管理特点",
            "description": "请描述移动应用开发中缺陷管理的特殊考虑。",
            "instructions": "说明移动应用特有的缺陷类型和管理挑战",
            "exercise_type": "text",
            "difficulty": "medium",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "特殊考虑：1.设备兼容性缺陷（多机型、多系统版本）；2.网络环境相关缺陷；3.性能和电量相关缺陷；4.应用商店审核相关问题；5.热更新机制影响。管理挑战：设备碎片化、复现困难、更新周期短、用户反馈渠道多"
        },
        {
            "title": "说明安全性缺陷的管理要点",
            "description": "请描述安全性缺陷的分类、优先级和处理流程。",
            "instructions": "说明安全缺陷的特殊性和管理要求",
            "exercise_type": "text",
            "difficulty": "hard",
            "category": "缺陷管理",
            "knowledge_point": "缺陷分类与优先级",
            "solution": "分类：注入漏洞、认证绕过、数据泄露、权限提升等。优先级：通常为高或紧急，需根据CVSS评分确定。处理流程：1.保密处理（避免泄露）；2.快速评估和响应；3.协调修复和发布；4.安全测试验证；5.事后分析和改进"
        }
    ]
}
