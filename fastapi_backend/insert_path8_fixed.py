#!/usr/bin/env python3
"""
学习路径8：测试计划编写与项目管理 - 50道精品题
基于测试计划编写与项目管理的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径8的50道精品题
exercises_data = [
    # ============ 测试计划概述（10题）============
    {
        "title": "关于测试计划（Test Plan），以下说法正确的是？",
        "description": "关于测试计划（Test Plan），以下说法正确的是？\n\nA. 测试计划是描述测试范围、方法、资源和进度的文档\nB. 测试计划只在大型项目中需要\nC. 测试计划一旦制定就不能修改\nD. 测试计划只由测试人员编写",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "测试计划概述",
    },
    {
        "title": "关于测试计划的编写者，以下说法正确的是？（多选）",
        "description": "关于测试计划的编写者，以下说法正确的是？（多选）\n\nA. 测试经理或测试负责人负责编写测试计划\nB. 测试计划的编写需要开发、测试、项目管理的多方参与\nC. 测试计划可以由测试团队成员共同编写\nD. 测试计划只由项目经理编写",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    {
        "title": "请判断：测试计划应该在需求分析完成后、测试执行开始前编写。",
        "description": "请判断：测试计划应该在需求分析完成后、测试执行开始前编写。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    {
        "title": "关于测试计划的作用，以下说法正确的是？",
        "description": "关于测试计划的作用，以下说法正确的是？\n\nA. 指导测试执行、控制测试进度、评估测试退出标准\nB. 测试计划没有实际作用，只是文档\nC. 测试计划只用于向客户展示\nD. 测试计划只用于测试人员内部沟通",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    {
        "title": "关于测试计划的版本控制，以下说法正确的是？（多选）",
        "description": "关于测试计划的版本控制，以下说法正确的是？（多选）\n\nA. 测试计划应该版本化，每次更新都要记录变更\nB. 测试计划的版本历史应该包含变更原因、变更内容、变更日期\nC. 测试计划一旦发布就不能再修改\nD. 测试计划的版本控制不重要，可以不记录",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试计划概述",
    },
    {
        "title": "请判断：测试计划应该根据项目风险来调整测试策略和资源分配。",
        "description": "请判断：测试计划应该根据项目风险来调整测试策略和资源分配。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    {
        "title": "关于测试计划的评审，以下说法正确的是？",
        "description": "关于测试计划的评审，以下说法正确的是？\n\nA. 测试计划应该经过多方评审（测试、开发、项目管理）\nB. 测试计划不需要评审，直接执行即可\nC. 测试计划只由测试人员评审\nD. 测试计划只由客户评审",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    {
        "title": "关于测试计划与测试策略的关系，以下说法正确的是？（多选）",
        "description": "关于测试计划与测试策略的关系，以下说法正确的是？（多选）\n\nA. 测试策略是高层面的指导方针，测试计划是具体的执行方案\nB. 测试策略通常包含在测试计划中\nC. 测试计划和测试策略是同一个文档\nD. 测试策略只关注[测什么]，测试计划关注[怎么测]",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试计划概述",
    },
    {
        "title": "请判断：测试计划应该在项目初期就完成，后续不能修改。",
        "description": "请判断：测试计划应该在项目初期就完成，后续不能修改。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    {
        "title": "关于测试计划的维护，以下说法正确的是？",
        "description": "关于测试计划的维护，以下说法正确的是？\n\nA. 测试计划应该随项目进展而更新，反映当前测试状态\nB. 测试计划制定后就不需要再维护\nC. 测试计划的维护只由测试经理负责\nD. 测试计划的维护成本太高，不建议维护",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划概述",
    },
    # ============ 测试计划的内容（15题）============
    {
        "title": "关于测试计划的测试范围（Test Scope），以下说法正确的是？",
        "description": "关于测试计划的测试范围（Test Scope），以下说法正确的是？\n\nA. 明确要测试什么、不测试什么、测试到什么程度\nB. 测试范围越大越好，覆盖所有功能\nC. 测试范围只由测试人员决定\nD. 测试范围不需要考虑项目风险",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的测试策略（Test Strategy），以下说法正确的是？（多选）",
        "description": "关于测试计划的测试策略（Test Strategy），以下说法正确的是？（多选）\n\nA. 描述测试的总体方法（如：黑盒测试、白盒测试、自动化测试）\nB. 测试策略应该考虑项目风险和技术复杂度\nC. 测试策略需要明确测试环境和测试数据需求\nD. 测试策略只关注功能测试，不关注非功能测试",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "请判断：测试计划中的测试交付物（Deliverables）包括测试报告、缺陷报告、测试数据等。",
        "description": "请判断：测试计划中的测试交付物（Deliverables）包括测试报告、缺陷报告、测试数据等。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的测试进度（Schedule），以下说法正确的是？",
        "description": "关于测试计划的测试进度（Schedule），以下说法正确的是？\n\nA. 应该定义测试里程碑、测试执行时间、测试报告时间\nB. 测试进度不重要，可以随意安排\nC. 测试进度只由测试人员决定，不需要考虑开发进度\nD. 测试进度应该尽可能紧凑，节省时间",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的测试资源（Resources），以下说法正确的是？（多选）",
        "description": "关于测试计划的测试资源（Resources），以下说法正确的是？（多选）\n\nA. 包括人力资源（测试人员数量、技能）、硬件资源、软件资源\nB. 测试资源的需求应该根据测试范围和进度来估算\nC. 测试资源可以随时增加，不需要提前规划\nD. 测试资源只包括人力资源，不包括硬件和软件",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "请判断：测试计划中的准入/准出标准（Entry/Exit Criteria）用于定义测试开始和结束的条件。",
        "description": "请判断：测试计划中的准入/准出标准（Entry/Exit Criteria）用于定义测试开始和结束的条件。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的测试环境（Test Environment），以下说法正确的是？",
        "description": "关于测试计划的测试环境（Test Environment），以下说法正确的是？\n\nA. 应该描述测试所需的硬件、软件、网络、数据环境\nB. 测试环境不重要，可以使用生产环境代替\nC. 测试环境只需要在测试执行前准备即可，不需要提前规划\nD. 测试环境只需要考虑功能测试，不需要考虑非功能测试",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的风险评估（Risk Assessment），以下说法正确的是？（多选）",
        "description": "关于测试计划的风险评估（Risk Assessment），以下说法正确的是？（多选）\n\nA. 应该识别项目风险、技术风险、资源风险，并制定应对措施\nB. 风险评估应该定期更新，反映项目当前状态\nC. 风险评估只由测试经理负责，不需要团队参与\nD. 风险评估不重要，可以跳过",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "请判断：测试计划中的缺陷管理（Defect Management）应该定义缺陷的生命周期、严重程度、优先级。",
        "description": "请判断：测试计划中的缺陷管理（Defect Management）应该定义缺陷的生命周期、严重程度、优先级。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的测试工具（Test Tools），以下说法正确的是？",
        "description": "关于测试计划的测试工具（Test Tools），以下说法正确的是？\n\nA. 应该明确要使用的测试工具（如：Selenium、JMeter、Postman）\nB. 测试工具的选择不重要，可以使用任何工具\nC. 测试工具只用于自动化测试，不用于手工测试\nD. 测试工具一旦选定就不能更换",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的测试培训（Training），以下说法正确的是？（多选）",
        "description": "关于测试计划的测试培训（Training），以下说法正确的是？（多选）\n\nA. 如果测试团队需要特定技能，应该在测试计划中明确培训需求\nB. 测试培训应该包括工具使用、业务流程、测试技术等方面\nC. 测试培训不重要，测试人员可以自学\nD. 测试培训只针对新入职的测试人员，不包括老员工",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "请判断：测试计划中的配置管理（Configuration Management）用于管理测试文档、测试脚本、测试数据的版本。",
        "description": "请判断：测试计划中的配置管理（Configuration Management）用于管理测试文档、测试脚本、测试数据的版本。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的沟通计划（Communication Plan），以下说法正确的是？",
        "description": "关于测试计划的沟通计划（Communication Plan），以下说法正确的是？\n\nA. 应该明确测试状态报告的频率、格式、接收人\nB. 沟通计划不重要，可以随意沟通\nC. 沟通计划只由测试经理制定，不需要考虑干系人需求\nD. 沟通计划只包括内部沟通，不包括外部沟通",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试计划的内容",
    },
    {
        "title": "关于测试计划的模板，以下说法正确的是？（多选）",
        "description": "关于测试计划的模板，以下说法正确的是？（多选）\n\nA. 测试计划应该使用组织标准的模板\nB. 测试计划模板可以根据项目特点进行调整\nC. 测试计划模板不重要，可以随意编写\nD. 测试计划模板应该包含必要的章节，但不应该过于僵化",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "测试计划的内容",
    },
    # ============ 测试进度与里程碑（10题）============
    {
        "title": "关于测试进度计划，以下说法正确的是？",
        "description": "关于测试进度计划，以下说法正确的是？\n\nA. 应该与开发进度协调，确保测试活动能在正确时间开始\nB. 测试进度可以独立制定，不需要考虑开发进度\nC. 测试进度一旦制定就不能修改\nD. 测试进度应该尽可能短，节省时间",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试进度与里程碑",
    },
    {
        "title": "关于测试里程碑（Milestone），以下说法正确的是？（多选）",
        "description": "关于测试里程碑（Milestone），以下说法正确的是？（多选）\n\nA. 测试里程碑包括：测试计划完成、测试环境就绪、测试执行开始、测试执行结束、测试报告发布\nB. 测试里程碑应该与项目整体里程碑对齐\nC. 测试里程碑可以根据项目进展动态调整\nD. 测试里程碑不重要，可以不需要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试进度与里程碑",
    },
    {
        "title": "请判断：测试进度应该使用甘特图（Gantt Chart）或类似工具来可视化。",
        "description": "请判断：测试进度应该使用甘特图（Gantt Chart）或类似工具来可视化。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试进度与里程碑",
    },
    {
        "title": "关于测试进度的监控，以下说法正确的是？",
        "description": "关于测试进度的监控，以下说法正确的是？\n\nA. 应该定期对比实际进度与计划进度，发现偏差并及时纠正\nB. 测试进度监控不重要，可以随意执行\nC. 测试进度监控只由测试经理负责\nD. 测试进度监控只需要在项目结束时进行",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试进度与里程碑",
    },
    {
        "title": "关于测试进度的风险，以下说法正确的是？（多选）",
        "description": "关于测试进度的风险，以下说法正确的是？（多选）\n\nA. 常见的测试进度风险包括：环境准备延迟、测试人员缺席、需求变更频繁\nB. 应该为测试进度风险制定应对措施\nC. 测试进度风险只由测试经理管理，不需要团队参与\nD. 测试进度风险不重要，可以不需要应对",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试进度与里程碑",
    },
    {
        "title": "请判断：测试进度应该预留缓冲时间（Buffer Time），以应对意外情况。",
        "description": "请判断：测试进度应该预留缓冲时间（Buffer Time），以应对意外情况。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试进度与里程碑",
    },
    {
        "title": "关于测试进度的报告，以下说法正确的是？",
        "description": "关于测试进度的报告，以下说法正确的是？\n\nA. 应该定期向项目干系人报告测试进度状态\nB. 测试进度报告不重要，可以不需要\nC. 测试进度报告只由测试经理编写\nD. 测试进度报告只需要在项目结束时编写",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试进度与里程碑",
    },
    {
        "title": "关于测试进度的变更管理，以下说法正确的是？（多选）",
        "description": "关于测试进度的变更管理，以下说法正确的是？（多选）\n\nA. 如果测试进度需要变更，应该评估影响并获得批准\nB. 测试进度变更应该记录并通知相关干系人\nC. 测试进度可以随时变更，不需要批准\nD. 测试进度变更只由测试经理决定",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试进度与里程碑",
    },
    {
        "title": "请判断：测试进度应该与开发进度、需求变更计划保持同步。",
        "description": "请判断：测试进度应该与开发进度、需求变更计划保持同步。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "测试进度与里程碑",
    },
    {
        "title": "关于测试进度的工具支持，以下说法正确的是？",
        "description": "关于测试进度的工具支持，以下说法正确的是？\n\nA. 可以使用项目管理工具（如：Jira、MS Project、Trello）来管理测试进度\nB. 测试进度管理不需要工具支持，可以手工管理\nC. 测试进度工具只用于大型项目，小型项目不需要\nD. 测试进度工具只由测试经理使用，普通测试人员不需要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试进度与里程碑",
    },
    # ============ 测试团队管理（10题）============
    {
        "title": "关于测试团队的组织结构，以下说法正确的是？",
        "description": "关于测试团队的组织结构，以下说法正确的是？\n\nA. 测试团队可以是职能型、项目型或矩阵型\nB. 测试团队只能采用一种组织结构\nC. 测试团队的组织结构不影响测试效率\nD. 测试团队不需要组织结构，可以随意安排",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试团队管理",
    },
    {
        "title": "关于测试人员的技能要求，以下说法正确的是？（多选）",
        "description": "关于测试人员的技能要求，以下说法正确的是？（多选）\n\nA. 测试人员需要具备业务知识、测试技术、沟通协调能力\nB. 测试人员的技能要求应该根据项目特点来明确\nC. 测试人员只需要会执行测试用例即可，不需要其他技能\nD. 测试人员的技能要求在不同项目中是相同的",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试团队管理",
    },
    {
        "title": "请判断：测试团队应该进行定期的培训和技术分享，提升团队整体能力。",
        "description": "请判断：测试团队应该进行定期的培训和技术分享，提升团队整体能力。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试团队管理",
    },
    {
        "title": "关于测试团队的绩效评估，以下说法正确的是？",
        "description": "关于测试团队的绩效评估，以下说法正确的是？\n\nA. 应该根据测试质量、测试效率、团队协作等方面评估\nB. 测试团队的绩效评估不重要，可以不需要\nC. 测试团队的绩效评估只关注缺陷数量\nD. 测试团队的绩效评估只由测试经理负责",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试团队管理",
    },
    {
        "title": "关于测试团队的沟通，以下说法正确的是？（多选）",
        "description": "关于测试团队的沟通，以下说法正确的是？（多选）\n\nA. 测试团队应该建立定期的沟通机制（如：每日站会、每周例会）\nB. 测试团队的沟通应该包括测试进度、缺陷状态、风险问题等方面\nC. 测试团队的沟通不重要，可以随意进行\nD. 测试团队的沟通只限于团队内部，不需要与外部沟通",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "测试团队管理",
    },
    {
        "title": "请判断：测试团队的规模应该根据项目规模、复杂度、时间要求来合理确定。",
        "description": "请判断：测试团队的规模应该根据项目规模、复杂度、时间要求来合理确定。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试团队管理",
    },
    {
        "title": "关于测试团队的角色分工，以下说法正确的是？",
        "description": "关于测试团队的角色分工，以下说法正确的是？\n\nA. 测试团队可以包括：测试经理、测试负责人、测试工程师、测试实习生\nB. 测试团队的所有成员都应该做相同的工作\nC. 测试团队的角色分工不重要，可以不需要\nD. 测试团队只需要的测试工程师，不需要其他角色",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试团队管理",
    },
    {
        "title": "关于测试团队的激励，以下说法正确的是？（多选）",
        "description": "关于测试团队的激励，以下说法正确的是？（多选）\n\nA. 应该通过认可、奖励、成长机会等方式激励测试团队\nB. 测试团队的激励应该公平、透明\nC. 测试团队的激励只通过薪资即可，不需要其他手段\nD. 测试团队的激励不重要，团队成员应该自觉工作",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试团队管理",
    },
    {
        "title": "请判断：测试团队应该定期进行团队建设活动，增强团队凝聚力。",
        "description": "请判断：测试团队应该定期进行团队建设活动，增强团队凝聚力。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "测试团队管理",
    },
    {
        "title": "关于测试团队的知识管理，以下说法正确的是？",
        "description": "关于测试团队的知识管理，以下说法正确的是？\n\nA. 应该建立测试知识库，积累测试经验、最佳实践、常见问题\nB. 测试团队的知识管理不重要，可以不需要\nC. 测试团队的知识管理只由测试经理负责\nD. 测试团队的知识管理只包括文档，不包括经验和技巧",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试团队管理",
    },
    # ============ 测试风险管理（6题）============
    {
        "title": "关于测试风险（Test Risk），以下说法正确的是？",
        "description": "关于测试风险（Test Risk），以下说法正确的是？\n\nA. 测试风险是指可能影响测试目标实现的不确定因素\nB. 测试风险只包括技术风险\nC. 测试风险无法管理，只能接受\nD. 测试风险不重要，可以不需要管理",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试风险管理",
    },
    {
        "title": "请判断：测试风险管理是一个持续的过程，应该贯穿整个项目生命周期。",
        "description": "请判断：测试风险管理是一个持续的过程，应该贯穿整个项目生命周期。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试风险管理",
    },
    {
        "title": "关于测试风险的识别，以下说法正确的是？（多选）",
        "description": "关于测试风险的识别，以下说法正确的是？（多选）\n\nA. 测试风险可以包括：进度风险、质量风险、资源风险、技术风险\nB. 测试风险的识别应该由整个测试团队参与\nC. 测试风险只由测试经理识别即可\nD. 测试风险识别只需要做一次，不需要定期更新",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试风险管理",
    },
    {
        "title": "请判断：测试风险应该根据可能性和影响程度进行优先级排序。",
        "description": "请判断：测试风险应该根据可能性和影响程度进行优先级排序。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试风险管理",
    },
    {
        "title": "关于测试风险的应对，以下说法正确的是？",
        "description": "关于测试风险的应对，以下说法正确的是？\n\nA. 可以通过规避、转移、减轻、接受等方式应对测试风险\nB. 测试风险只能接受，无法应对\nC. 测试风险应对只由测试经理负责\nD. 测试风险应对不需要成本考虑",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试风险管理",
    },
    {
        "title": "关于测试风险的监控，以下说法正确的是？（多选）",
        "description": "关于测试风险的监控，以下说法正确的是？（多选）\n\nA. 应该定期监控测试风险的状态，评估应对措施的有效性\nB. 测试风险的监控应该贯穿整个项目生命周期\nC. 测试风险的监控只需要在项目初期进行\nD. 测试风险的监控不重要，可以不需要",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试风险管理",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径8的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 8")
    print("🗑️  已删除学习路径8（测试计划编写与项目管理）的旧习题")

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
                VALUES (?, ?, ?, ?, ?, 8, ?, 1, ?, datetime('now'), datetime('now'))
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 8", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径8（测试计划编写与项目管理）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 8")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径8现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
