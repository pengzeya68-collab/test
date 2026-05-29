#!/usr/bin/env python3
"""
学习路径7：缺陷管理与追踪 - 50道精品题
基于缺陷管理与追踪的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径7的50道精品题
exercises_data = [
    # ============ 缺陷基础概念（10题）============
    {
        "title": "关于软件缺陷（Defect/Bug），以下说法正确的是？",
        "description": "关于软件缺陷（Defect/Bug），以下说法正确的是？\n\nA. 软件缺陷是指软件产品中存在的、导致系统不能正常工作的问题\nB. 软件缺陷只包括功能错误，不包括性能问题\nC. 所有的软件缺陷都可以通过穷举测试发现\nD. 软件缺陷就是调试（Debug），目的是修复缺陷",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "缺陷基础概念",
    },
    {
        "title": "关于缺陷的生命周期，以下说法正确的是？（多选）",
        "description": "关于缺陷的生命周期，以下说法正确的是？（多选）\n\nA. 新建（New）→ 打开/分配（Open）→ 已修复（Fixed）→ 已验证（Verified）→ 关闭（Closed）\nB. 如果验证不通过，可以重新打开（Reopened）\nC. 开发人员可以拒绝缺陷（Rejected），如果是重复提交或不是缺陷\nD. 缺陷一旦关闭就不能再重新打开",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷基础概念",
    },
    {
        "title": "请判断：缺陷（Bug）和增强需求（Enhancement）是同一个概念，没有区别。",
        "description": "请判断：缺陷（Bug）和增强需求（Enhancement）是同一个概念，没有区别。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷基础概念",
    },
    {
        "title": "关于缺陷的严重级别（Severity），以下说法正确的是？",
        "description": "关于缺陷的严重级别（Severity），以下说法正确的是？\n\nA. 致命（Blocker/Critical）：系统崩溃、数据丢失、安全问题\nB. 严重（Major）：主要功能错误，严重影响使用\nC. 一般（Minor）：次要功能错误，有替代方案\nD. 轻微（Trivial）：界面错字、排版问题",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷基础概念",
    },
    {
        "title": "关于缺陷的优先级（Priority），以下说法正确的是？（多选）",
        "description": "关于缺陷的优先级（Priority），以下说法正确的是？（多选）\n\nA. P0-立即：必须立即修复\nB. P1-高：应尽快在下一个版本中修复\nC. P2-中：按正常排期\nD. P3-低：可以延后修复",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷基础概念",
    },
    {
        "title": "请判断：严重级别（Severity）和优先级（Priority）是正相关的，即严重程度高的缺陷一定优先修复。",
        "description": "请判断：严重级别（Severity）和优先级（Priority）是正相关的，即严重程度高的缺陷一定优先修复。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷基础概念",
    },
    {
        "title": "关于缺陷的严重级别和优先级的关系，以下说法正确的是？",
        "description": "关于缺陷的严重级别和优先级的关系，以下说法正确的是？\n\nA. 严重级别描述缺陷的技术影响，优先级描述业务上的修复紧迫性\nB. 严重级别和优先级总是相同的\nC. 严重级别高的缺陷一定优先修复\nD. 优先级高的缺陷一定严重级别高",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷基础概念",
    },
    {
        "title": "关于缺陷的属性，以下说法正确的是？（多选）",
        "description": "关于缺陷的属性，以下说法正确的是？（多选）\n\nA. 缺陷ID：唯一标识缺陷\nB. 缺陷标题：简要描述缺陷\nC. 缺陷描述：详细描述缺陷现象、复现步骤等\nD. 附件：截图、日志、复现视频等",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷基础概念",
    },
    {
        "title": "请判断：一个缺陷应该只修复一个问题，不要在一个缺陷中修复多个不相关的问题。",
        "description": "请判断：一个缺陷应该只修复一个问题，不要在一个缺陷中修复多个不相关的问题。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷基础概念",
    },
    {
        "title": "关于缺陷的类型，以下说法正确的是？",
        "description": "关于缺陷的类型，以下说法正确的是？\n\nA. 功能缺陷：系统功能不符合需求\nB. 性能缺陷：系统响应时间过长、吞吐量不足等\nC. 安全缺陷：权限绕过、SQL注入、XSS等\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷基础概念",
    },
    # ============ 缺陷报告编写（10题）============
    {
        "title": "关于好的缺陷报告，以下说法正确的是？",
        "description": "关于好的缺陷报告，以下说法正确的是？\n\nA. 应该清晰、准确、完整、可复现\nB. 只需要简单描述一下就可以了\nC. 应该包含尽可能多的技术术语\nD. 应该包含情感色彩，强调问题的严重性",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "关于缺陷报告的要素，以下说法正确的是？（多选）",
        "description": "关于缺陷报告的要素，以下说法正确的是？（多选）\n\nA. 标题：简要描述缺陷\nB. 复现步骤：详细描述如何复现缺陷\nC. 预期结果 vs 实际结果：描述应该发生什么 vs 实际发生了什么\nD. 环境信息：操作系统、浏览器、设备型号等",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "请判断：缺陷报告的复现步骤应该是「可复现的」，即任何人按照步骤都能复现该缺陷。",
        "description": "请判断：缺陷报告的复现步骤应该是「可复现的」，即任何人按照步骤都能复现该缺陷。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "关于缺陷报告的「预期结果」和「实际结果」，以下说法正确的是？",
        "description": "关于缺陷报告的「预期结果」和「实际结果」，以下说法正确的是？\n\nA. 预期结果描述「应该发生什么」，实际结果描述「实际发生了什么」\nB. 预期结果描述「实际发生了什么」，实际结果描述「应该发生什么」\nC. 只需要描述实际结果即可\nD. 预期结果和实际结果不需要对比",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "关于缺陷报告的附件，以下说法正确的是？（多选）",
        "description": "关于缺陷报告的附件，以下说法正确的是？（多选）\n\nA. 截图应该包含关键区域，并用红框标注问题点\nB. 日志文件应该包含错误发生前后的日志\nC. 视频可以直观地展示复现步骤\nD. 附件越多越好，不需要筛选",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷报告编写",
    },
    {
        "title": "请判断：缺陷报告的标题应该尽可能详细，包含所有的细节信息。",
        "description": "请判断：缺陷报告的标题应该尽可能详细，包含所有的细节信息。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷报告编写",
    },
    {
        "title": "关于缺陷报告的「环境信息」，以下说法正确的是？",
        "description": "关于缺陷报告的「环境信息」，以下说法正确的是？\n\nA. 应该包含操作系统、浏览器版本、设备型号、网络环境等\nB. 环境信息不重要，不需要填写\nC. 只需要填写操作系统即可\nD. 环境信息只需要开发人员自己猜",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "关于缺陷报告的语言，以下说法正确的是？（多选）",
        "description": "关于缺陷报告的语言，以下说法正确的是？（多选）\n\nA. 应该使用清晰、准确的语言\nB. 应该避免模糊的词汇（如「有时候」、「可能」）\nC. 应该包含足够的细节，让开发人员能理解问题\nD. 应该使用情感色彩的语言，强调问题的严重性",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "请判断：如果一个缺陷无法复现，就不应该提交缺陷报告。",
        "description": "请判断：如果一个缺陷无法复现，就不应该提交缺陷报告。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    {
        "title": "关于缺陷报告的最佳实践，以下说法正确的是？",
        "description": "关于缺陷报告的最佳实践，以下说法正确的是？\n\nA. 一个缺陷报告只报告一个缺陷\nB. 可以在一个缺陷报告中包含多个不相关的问题\nC. 缺陷报告的标题越长越好\nD. 不需要提供复现步骤，开发人员自己会找到问题",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷报告编写",
    },
    # ============ 缺陷管理流程（10题）============
    {
        "title": "关于缺陷管理流程，以下说法正确的是？",
        "description": "关于缺陷管理流程，以下说法正确的是？\n\nA. 测试人员发现缺陷 → 提交缺陷报告 → 开发人员修复 → 测试人员验证 → 关闭缺陷\nB. 测试人员发现缺陷 → 直接修复 → 关闭缺陷\nC. 测试人员发现缺陷 → 不需要提交报告，口头告诉开发人员即可\nD. 缺陷修复后不需要验证，直接关闭",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理流程",
    },
    {
        "title": "关于缺陷的分派（Assignment），以下说法正确的是？（多选）",
        "description": "关于缺陷的分派（Assignment），以下说法正确的是？（多选）\n\nA. 测试经理或开发经理根据缺陷类型和模块，分派给相应的开发人员\nB. 缺陷应该分派给正确的负责人，避免无效沟通\nC. 如果不确定应该分派给谁，可以分派给团队负责人\nD. 缺陷分派后就不能再修改",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷管理流程",
    },
    {
        "title": "请判断：缺陷修复后，应该由开发人员自己验证，不需要测试人员参与。",
        "description": "请判断：缺陷修复后，应该由开发人员自己验证，不需要测试人员参与。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷管理流程",
    },
    {
        "title": "关于缺陷的验证（Verification），以下说法正确的是？",
        "description": "关于缺陷的验证（Verification），以下说法正确的是？\n\nA. 验证缺陷是否真正被修复了，而不是仅仅检查代码是否改动\nB. 只需要检查代码是否改动了即可\nC. 验证只需要做一次即可\nD. 验证不需要在原环境下进行",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷管理流程",
    },
    {
        "title": "关于缺陷的重新打开（Reopen），以下说法正确的是？（多选）",
        "description": "关于缺陷的重新打开（Reopen），以下说法正确的是？（多选）\n\nA. 如果验证不通过，测试人员应该重新打开缺陷\nB. 重新打开缺陷时，应该说明验证不通过的原因\nC. 重新打开缺陷后，开发人员需要继续修复\nD. 一旦关闭的缺陷就不能再重新打开",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷管理流程",
    },
    {
        "title": "请判断：缺陷管理工具（如Jira、Bugzilla）可以帮助团队跟踪缺陷的生命周期。",
        "description": "请判断：缺陷管理工具（如Jira、Bugzilla）可以帮助团队跟踪缺陷的生命周期。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷管理流程",
    },
    {
        "title": "关于缺陷管理工具的功能，以下说法正确的是？",
        "description": "关于缺陷管理工具的功能，以下说法正确的是？\n\nA. 缺陷管理工具支持缺陷的创建、分派、跟踪、报告等功能\nB. 缺陷管理工具只能用于记录缺陷，不能生成报告\nC. 缺陷管理工具不需要权限管理\nD. 缺陷管理工具不能集成到CI/CD流程中",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理流程",
    },
    {
        "title": "关于缺陷的度量指标，以下说法正确的是？（多选）",
        "description": "关于缺陷的度量指标，以下说法正确的是？（多选）\n\nA. 缺陷密度：每千行代码中的缺陷数\nB. 缺陷去除率：在某个阶段发现的缺陷数 / 该阶段注入的缺陷总数\nC. 平均修复时间：从缺陷报告到缺陷修复的时间\nD. 缺陷复现率：复现的缺陷数 / 提交的缺陷总数",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷管理流程",
    },
    {
        "title": "请判断：缺陷的密度越低，说明软件的质量越高。",
        "description": "请判断：缺陷的密度越低，说明软件的质量越高。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "缺陷管理流程",
    },
    {
        "title": "关于缺陷的趋势分析，以下说法正确的是？",
        "description": "关于缺陷的趋势分析，以下说法正确的是？\n\nA. 缺陷趋势分析可以帮助预测软件的质量趋势和发布时间\nB. 缺陷趋势分析没有用，不需要做\nC. 缺陷趋势分析只需要关注缺陷总数\nD. 缺陷趋势分析不能用于发布决策",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷管理流程",
    },
    # ============ 缺陷管理工具（10题）============
    {
        "title": "关于常见的缺陷管理工具，以下说法正确的是？",
        "description": "关于常见的缺陷管理工具，以下说法正确的是？\n\nA. Jira：功能强大，支持自定义工作流，常用于敏捷团队\nB. Bugzilla：开源工具，功能简单\nC. Redmine：开源工具，支持项目管理和缺陷跟踪\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理工具",
    },
    {
        "title": "关于Jira的使用，以下说法正确的是？（多选）",
        "description": "关于Jira的使用，以下说法正确的是？（多选）\n\nA. 可以创建自定义字段和工作流\nB. 可以生成各种类型的报告（如缺陷趋势图、燃尽图）\nC. 可以集成到CI/CD流程中（如Jenkins、Git）\nD. Jira只能用于缺陷管理，不能用于项目管理",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷管理工具",
    },
    {
        "title": "请判断：在Jira中，缺陷（Issue）的类型可以包括：Bug、Story、Task、Epic等。",
        "description": "请判断：在Jira中，缺陷（Issue）的类型可以包括：Bug、Story、Task、Epic等。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷管理工具",
    },
    {
        "title": "关于缺陷管理工具的权限管理，以下说法正确的是？",
        "description": "关于缺陷管理工具的权限管理，以下说法正确的是？\n\nA. 应该为不同角色（测试人员、开发人员、测试经理、开发经理）设置不同的权限\nB. 所有人都应该有管理员权限\nC. 权限管理不重要，不需要设置\nD. 只有测试人员才能提交缺陷",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理工具",
    },
    {
        "title": "关于缺陷管理工具的搜索和过滤，以下说法正确的是？（多选）",
        "description": "关于缺陷管理工具的搜索和过滤，以下说法正确的是？（多选）\n\nA. 可以根据缺陷ID、标题、状态、严重级别、优先级等条件搜索\nB. 可以保存常用的搜索条件为过滤器\nC. 可以导出搜索结果为Excel或CSV\nD. 搜索功能不重要，不需要使用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "缺陷管理工具",
    },
    {
        "title": "请判断：缺陷管理工具中的「仪表盘（Dashboard）」可以直观展示团队的缺陷状况。",
        "description": "请判断：缺陷管理工具中的「仪表盘（Dashboard）」可以直观展示团队的缺陷状况。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷管理工具",
    },
    {
        "title": "关于缺陷管理工具的集成，以下说法正确的是？",
        "description": "关于缺陷管理工具的集成，以下说法正确的是？\n\nA. 可以集成版本控制系统（如Git），关联代码提交和缺陷\nB. 可以集成CI/CD工具（如Jenkins），在构建失败时自动创建缺陷\nC. 可以集成聊天工具（如Slack），在缺陷状态变更时发送通知\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷管理工具",
    },
    {
        "title": "关于缺陷管理工具的报告功能，以下说法正确的是？（多选）",
        "description": "关于缺陷管理工具的报告功能，以下说法正确的是？（多选）\n\nA. 可以生成缺陷趋势图、缺陷分布图、缺陷年龄报告等\nB. 报告可以帮助管理层了解项目质量和风险\nC. 可以导出报告为PDF、Excel等格式\nD. 报告功能不重要，不需要使用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷管理工具",
    },
    {
        "title": "请判断：缺陷管理工具应该定期备份，防止数据丢失。",
        "description": "请判断：缺陷管理工具应该定期备份，防止数据丢失。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷管理工具",
    },
    {
        "title": "关于缺陷管理工具的选择，以下说法正确的是？",
        "description": "关于缺陷管理工具的选择，以下说法正确的是？\n\nA. 应该根据团队规模、开发模式、预算、功能需求等因素选择合适的工具\nB. 越贵的工具越好\nC. 开源工具一定比商业工具差\nD. 工具的选择不影响团队的协作效率",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理工具",
    },
    # ============ 缺陷预防与过程改进（10题）============
    {
        "title": "关于缺陷预防，以下说法正确的是？",
        "description": "关于缺陷预防，以下说法正确的是？\n\nA. 缺陷预防是指在缺陷产生之前就发现并纠正问题\nB. 缺陷预防是不可能的，只需要关注缺陷修复\nC. 缺陷预防只适用于需求阶段\nD. 缺陷预防成本比缺陷修复成本高",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "关于早期测试（Early Testing），以下说法正确的是？（多选）",
        "description": "关于早期测试（Early Testing），以下说法正确的是？（多选）\n\nA. 在需求阶段就参与评审，发现需求中的缺陷\nB. 在设计阶段就参与评审，发现设计中的缺陷\nC. 早期测试可以大幅降低缺陷修复成本\nD. 测试只需要在编码完成后进行",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "请判断：根据缺陷修复成本曲线，在需求阶段发现的缺陷，修复成本是最低的。",
        "description": "请判断：根据缺陷修复成本曲线，在需求阶段发现的缺陷，修复成本是最低的。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "关于根因分析（Root Cause Analysis），以下说法正确的是？",
        "description": "关于根因分析（Root Cause Analysis），以下说法正确的是？\n\nA. 根因分析用于找到缺陷的根本原因，而不是表面原因\nB. 根因分析只需要修复表面问题即可\nC. 根因分析不适用于软件测试\nD. 根因分析会增加缺陷修复成本",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "关于5 Whys（五次为什么）分析法，以下说法正确的是？（多选）",
        "description": "关于5 Whys（五次为什么）分析法，以下说法正确的是？（多选）\n\nA. 通过连续问5次「为什么」，找到缺陷的根本原因\nB. 5 Whys可以用于团队复盘会议（Retrospective）\nC. 5 Whys不仅适用于技术问题，也适用于过程问题\nD. 5 Whys只能用于分析技术缺陷",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "请判断：缺陷预防比缺陷修复更重要，因为预防可以避免缺陷的产生。",
        "description": "请判断：缺陷预防比缺陷修复更重要，因为预防可以避免缺陷的产生。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "关于过程改进（Process Improvement），以下说法正确的是？",
        "description": "关于过程改进（Process Improvement），以下说法正确的是？\n\nA. 过程改进用于优化软件开发流程，减少缺陷注入\nB. 过程改进只需要关注测试方法\nC. 过程改进会增加开发成本，不值得\nD. 过程改进不适用于敏捷开发",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "关于缺陷管理的度量指标，以下说法正确的是？（多选）",
        "description": "关于缺陷管理的度量指标，以下说法正确的是？（多选）\n\nA. 缺陷去除率（DRE）：在某个阶段发现的缺陷数 / 该阶段注入的缺陷总数\nB. 缺陷泄漏率：在后续阶段发现的缺陷数 / 该阶段注入的缺陷总数\nC. 平均修复时间（MTTR）：从缺陷报告到缺陷修复的时间\nD. 缺陷复现率：复现的缺陷数 / 提交的缺陷总数",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "请判断：缺陷管理的目标不仅仅是修复缺陷，还包括预防缺陷、改进过程。",
        "description": "请判断：缺陷管理的目标不仅仅是修复缺陷，还包括预防缺陷、改进过程。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "缺陷预防与过程改进",
    },
    {
        "title": "关于测试团队的缺陷管理职责，以下说法正确的是？",
        "description": "关于测试团队的缺陷管理职责，以下说法正确的是？\n\nA. 测试人员负责发现缺陷、报告缺陷、验证缺陷修复\nB. 测试人员不需要参与缺陷预防\nC. 测试人员只需要关注缺陷修复，不需要关注过程改进\nD. 测试人员在缺陷管理中没有责任",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "缺陷预防与过程改进",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径7的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 7")
    print("🗑️  已删除学习路径7（缺陷管理与追踪）的旧习题")

    # 插入50道精品题
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"

            cursor.execute(
                """
                INSERT INTO exercises 
                (title, description, solution, exercise_type, difficulty, 
                 learning_path_id, category, is_public, language, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 7, ?, 1, ?, datetime('now'), datetime('now'))
            """,
                (
                    ex["title"],
                    ex["description"],
                    ex["solution"],
                    ex["exercise_type"],
                    ex["difficulty"],
                    ex["category"],
                    lang,
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"⚠️  插入失败: {e}")
            continue

    conn.commit()

    # 更新 learning_paths 的 exercise_count
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 7", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径7（缺陷管理与追踪）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 7")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径7现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
