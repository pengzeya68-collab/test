#!/usr/bin/env python3
"""
手动编写高质量习题 - 基于真实课程内容
学习路径1：软件测试基础理论
课程内容：5个章节，包含定义、原则、模型、分类、缺陷管理
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 基于真实课程内容的50道精品题
exercises_data = [
    # ============ 第1节：软件测试的定义与目的 (10题) ============
    {
        "title": "以下对软件测试的定义，正确的是？",
        "description": "以下对软件测试的定义，正确的是？\n\nA. 软件测试是使用人工或自动手段来运行或测定某个系统的过程，目的在于检验它是否满足规定的需求，或弄清预期结果与实际结果之间的差别。\nB. 软件测试是为了证明程序没有错误的过程。\nC. 软件测试就是调试（Debug），目的是修复缺陷。\nD. 软件测试只在编码完成后进行。",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "软件测试的核心目的包括以下哪些？（多选）",
        "description": "软件测试的核心目的包括以下哪些？（多选）\n\nA. 发现缺陷（Find Bugs）\nB. 验证需求（Verify Requirements）\nC. 证明软件没有任何缺陷\nD. 评估质量（Assess Quality）",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "请判断：测试只能证明缺陷存在，而不能证明缺陷不存在。",
        "description": "请判断：测试只能证明缺陷存在，而不能证明缺陷不存在。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "关于「验证（Verification）」和「确认（Validation）」，以下说法正确的是？",
        "description": "关于「验证（Verification）」和「确认（Validation）」，以下说法正确的是？\n\nA. 验证：我们正确地建造产品了吗？确认：我们建造了正确的产品吗？\nB. 验证：我们建造了正确的产品吗？确认：我们正确地建造产品了吗？\nC. 验证和确认是同一个概念，没有区别。\nD. 验证和确认都只关注最终结果。",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "测试与调试的区别包括以下哪些？（多选）",
        "description": "测试与调试的区别包括以下哪些？（多选）\n\nA. 测试的目的是发现缺陷，调试的目的是定位并修复缺陷\nB. 测试由测试人员执行，调试由开发人员执行\nC. 测试贯穿整个开发过程，调试主要在编码阶段\nD. 测试和调试是同一个过程，没有区别",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "请判断：通过早期介入测试（如需求评审、设计评审），可以在缺陷产生之前就发现并纠正问题，大幅降低修复成本。",
        "description": "请判断：通过早期介入测试（如需求评审、设计评审），可以在缺陷产生之前就发现并纠正问题，大幅降低修复成本。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "软件测试为项目干系人提供关于软件质量的客观信息，这些信息包括？",
        "description": "软件测试为项目干系人提供关于软件质量的客观信息，这些信息包括？\n\nA. 缺陷密度、通过率等指标\nB. 只有缺陷数量\nC. 只有测试通过的用例数量\nD. 不需要提供任何信息",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "关于软件测试的目的，以下说法错误的是？",
        "description": "关于软件测试的目的，以下说法错误的是？\n\nA. 软件测试可以证明软件没有任何缺陷\nB. 软件测试可以发现软件中存在的缺陷\nC. 软件测试可以评估软件的质量\nD. 软件测试可以验证软件是否满足需求",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "请判断：验证（Verification）关注过程，如评审、走查；确认（Validation）关注结果，如系统测试、验收测试。",
        "description": "请判断：验证（Verification）关注过程，如评审、走查；确认（Validation）关注结果，如系统测试、验收测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "软件测试的定义与目的",
    },
    {
        "title": "软件测试的定义中，'弄清预期结果与实际结果之间的差别'指的是？",
        "description": "软件测试的定义中，'弄清预期结果与实际结果之间的差别'指的是？\n\nA. 比较软件的预期行为与实际行为，发现不一致\nB. 比较不同版本软件的性能\nC. 比较不同测试方法的效率\nD. 比较开发与测试的工作量",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "软件测试的定义与目的",
    },
    # ============ 第2节：测试的七大原则 (15题) ============
    {
        "title": "ISTQB定义的测试七大原则中，原则1是？",
        "description": "ISTQB定义的测试七大原则中，原则1是？\n\nA. 测试说明存在缺陷（Testing shows the presence of defects）\nB. 穷尽测试是可能的\nC. 测试可以证明没有缺陷\nD. 测试应该在编码完成后开始",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试的七大原则",
    },
    {
        "title": "关于「穷尽测试是不可能的」这一原则，以下说法正确的是？",
        "description": "关于「穷尽测试是不可能的」这一原则，以下说法正确的是？\n\nA. 除了极其简单的小程序，想测试所有输入组合和前置条件是不可能的\nB. 只要时间足够，穷尽测试是可以实现的\nC. 穷尽测试是必要的，否则不能保证质量\nD. 穷尽测试只适用于大型系统",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试的七大原则",
    },
    {
        "title": "测试七大原则中，关于修复成本递增规律，以下说法正确的是？（多选）",
        "description": "测试七大原则中，关于修复成本递增规律，以下说法正确的是？（多选）\n\nA. 需求阶段发现缺陷：修复成本 = 1x\nB. 设计阶段发现缺陷：修复成本 = 10x\nC. 编码阶段发现缺陷：修复成本 = 50x\nD. 生产环境发现缺陷：修复成本 = 1000x",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试的七大原则",
    },
    {
        "title": "请判断：根据缺陷集群性（Defect Clustering）原则，80%的缺陷通常只存在于20%的模块中。",
        "description": "请判断：根据缺陷集群性（Defect Clustering）原则，80%的缺陷通常只存在于20%的模块中。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试的七大原则",
    },
    {
        "title": "关于「杀虫剂悖论（Pesticide Paradox）」，以下说法正确的是？",
        "description": "关于「杀虫剂悖论（Pesticide Paradox）」，以下说法正确的是？\n\nA. 如果反复使用相同的测试用例集，最终将无法发现新的缺陷\nB. 测试用例应该像杀虫剂一样越强越好\nC. 测试用例一旦写好就不需要修改\nD. 杀虫剂悖论与软件测试无关",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试的七大原则",
    },
    {
        "title": "测试七大原则中，「测试依赖于上下文」的含义是？",
        "description": "测试七大原则中，「测试依赖于上下文」的含义是？\n\nA. 不同类型的软件需要不同的测试方法\nB. 所有软件的测试方法都是一样的\nC. 测试只依赖于开发者的经验\nD. 测试只依赖于项目的预算",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试的七大原则",
    },
    {
        "title": "关于「没有缺陷就是好用？」这一原则，以下说法正确的是？（多选）",
        "description": "关于「没有缺陷就是好用？」这一原则，以下说法正确的是？（多选）\n\nA. 即使软件没有缺陷，也不代表它满足用户需求\nB. 测试不仅要找Bug，还要验证需求\nC. 只要没有缺陷，软件就是好用的\nD. 没有缺陷的软件一定满足用户需求",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试的七大原则",
    },
    {
        "title": "请判断：测试可以证明软件中没有缺陷。",
        "description": "请判断：测试可以证明软件中没有缺陷。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "测试的七大原则",
    },
    {
        "title": "ISTQB七大原则中，关于早期测试的原则说明？",
        "description": "ISTQB七大原则中，关于早期测试的原则说明？\n\nA. 测试活动应尽早开始，缺陷发现得越早，修复成本越低\nB. 测试应该在编码完成后开始\nC. 测试应该在系统测试阶段开始\nD. 测试开始的时间不影响修复成本",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "测试的七大原则",
    },
    {
        "title": "关于杀虫剂悖论的解决方法，以下说法正确的是？",
        "description": "关于杀虫剂悖论的解决方法，以下说法正确的是？\n\nA. 定期审查和修订测试用例\nB. 永远使用相同的测试用例\nC. 不需要修改测试用例\nD. 只使用自动化测试",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试的七大原则",
    },
    {
        "title": "请判断：电商网站和航空控制系统的测试策略可以完全相同。",
        "description": "请判断：电商网站和航空控制系统的测试策略可以完全相同。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "测试的七大原则",
    },
    {
        "title": "ISTQB七大原则包括哪些？（多选）",
        "description": "ISTQB七大原则包括哪些？（多选）\n\nA. 测试说明存在缺陷\nB. 穷尽测试是不可能的\nC. 早期测试\nD. 测试可以证明没有缺陷",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试的七大原则",
    },
    {
        "title": "关于缺陷集群性（Defect Clustering），以下说法正确的是？",
        "description": "关于缺陷集群性（Defect Clustering），以下说法正确的是？\n\nA. 大部分缺陷往往集中在少部分模块中\nB. 缺陷均匀分布在所有模块中\nC. 每个模块的缺陷数量都相同\nD. 缺陷集群性不适用于大型系统",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试的七大原则",
    },
    {
        "title": "请判断：根据早期测试原则，在需求阶段发现的缺陷，修复成本是编码阶段发现缺陷的50倍。",
        "description": "请判断：根据早期测试原则，在需求阶段发现的缺陷，修复成本是编码阶段发现缺陷的50倍。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "测试的七大原则",
    },
    # ============ 第3节：软件开发生命周期与测试模型 (10题) ============
    {
        "title": "关于瀑布模型（Waterfall Model），以下说法正确的是？",
        "description": "关于瀑布模型（Waterfall Model），以下说法正确的是？\n\nA. 测试只在编码完成后进行，返工成本很高\nB. 测试贯穿整个开发过程\nC. 需求变更非常容易\nD. 瀑布模型是目前最流行的开发模型",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "V模型中，测试活动与开发活动的对应关系是？",
        "description": "V模型中，测试活动与开发活动的对应关系是？\n\nA. 需求分析←→验收测试，概要设计←→系统测试，详细设计←→集成测试，编码←→单元测试\nB. 需求分析←→单元测试，概要设计←→集成测试，详细设计←→系统测试，编码←→验收测试\nC. V模型中没有对应关系\nD. V模型中只有编码和单元测试对应",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "关于敏捷开发中的测试，以下说法正确的有？（多选）",
        "description": "关于敏捷开发中的测试，以下说法正确的有？（多选）\n\nA. 持续测试：每天都在进行测试\nB. 自动化优先：自动化测试是敏捷的基石\nC. 测试驱动开发（TDD）：先写测试再写代码\nD. 敏捷开发中不需要测试",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "请判断：TDD（测试驱动开发）的「红-绿-重构」循环中，「红」代表编写一个失败的测试用例。",
        "description": "请判断：TDD（测试驱动开发）的「红-绿-重构」循环中，「红」代表编写一个失败的测试用例。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "关于V模型，以下说法正确的是？",
        "description": "关于V模型，以下说法正确的是？\n\nA. 仍然是线性模型，需求变更困难\nB. 可以轻松应对需求变更\nC. 测试贯穿整个开发过程\nD. V模型是最快的开发模型",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "W模型（W-Model）在V模型基础上强调了什么？",
        "description": "W模型（W-Model）在V模型基础上强调了什么？\n\nA. 测试应该伴随着整个开发过程，不仅要对代码进行测试，还要对需求和设计进行测试\nB. 只需要对代码进行测试\nC. 测试只在编码完成后进行\nD. W模型与V模型没有区别",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "关于TDD的「红-绿-重构」循环，以下说法正确的是？（多选）",
        "description": "关于TDD的「红-绿-重构」循环，以下说法正确的是？（多选）\n\nA. 红：编写一个失败的测试用例\nB. 绿：编写最少的代码让测试通过\nC. 重构：优化代码结构，保持测试通过\nD. 红：编写通过的测试用例",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "请判断：敏捷开发中，自动化测试是敏捷的基石。",
        "description": "请判断：敏捷开发中，自动化测试是敏捷的基石。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "关于集成测试的策略，以下说法正确的是？",
        "description": "关于集成测试的策略，以下说法正确的是？\n\nA. 自顶向下：从顶层模块开始，使用桩模块\nB. 自顶向下：从底层模块开始，使用驱动模块\nC. 自底向上：从顶层模块开始，使用桩模块\nD. 大爆炸集成是推荐的方法",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "软件开发生命周期与测试模型",
    },
    {
        "title": "请判断：BDD（行为驱动开发）使用自然语言描述测试场景。",
        "description": "请判断：BDD（行为驱动开发）使用自然语言描述测试场景。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "软件开发生命周期与测试模型",
    },
    # ============ 第4节：测试分类体系 (10题) ============
    {
        "title": "关于单元测试（Unit Testing），以下说法正确的是？",
        "description": "关于单元测试（Unit Testing），以下说法正确的是？\n\nA. 对软件的最小可测试单元（函数、方法、类）进行测试，通常由开发人员编写和执行\nB. 对整个系统进行测试\nC. 只对用户界面进行测试\nD. 单元测试不需要自动化",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "测试分类体系",
    },
    {
        "title": "按测试阶段分类，测试可以分为以下哪些类型？（多选）",
        "description": "按测试阶段分类，测试可以分为以下哪些类型？（多选）\n\nA. 单元测试（Unit Testing）\nB. 集成测试（Integration Testing）\nC. 系统测试（System Testing）\nD. 验收测试（Acceptance Testing）",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "测试分类体系",
    },
    {
        "title": "关于黑盒测试和白盒测试的区别，以下说法正确的是？",
        "description": "关于黑盒测试和白盒测试的区别，以下说法正确的是？\n\nA. 黑盒测试不关心内部结构，只关注输入和输出；白盒测试基于代码内部逻辑\nB. 黑盒测试基于代码内部逻辑，白盒测试不关心内部结构\nC. 黑盒测试和白盒测试是同一个概念\nD. 黑盒测试只适用于单元测试",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试分类体系",
    },
    {
        "title": "请判断：灰盒测试（Gray-box Testing）介于黑盒和白盒之间，了解部分内部结构但主要从外部测试。",
        "description": "请判断：灰盒测试（Gray-box Testing）介于黑盒和白盒之间，了解部分内部结构但主要从外部测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试分类体系",
    },
    {
        "title": "关于验收测试（Acceptance Testing），以下说法正确的是？（多选）",
        "description": "关于验收测试（Acceptance Testing），以下说法正确的是？（多选）\n\nA. Alpha测试：在开发环境中由用户进行\nB. Beta测试：在用户实际环境中进行\nC. UAT（用户验收测试）：正式的业务验收\nD. 验收测试由开发人员执行",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "测试分类体系",
    },
    {
        "title": "白盒测试的覆盖标准包括以下哪些？（多选）",
        "description": "白盒测试的覆盖标准包括以下哪些？（多选）\n\nA. 语句覆盖\nB. 判定覆盖\nC. 条件覆盖\nD. 路径覆盖",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试分类体系",
    },
    {
        "title": "请判断：集成测试是测试多个单元/模块之间的交互是否正确。",
        "description": "请判断：集成测试是测试多个单元/模块之间的交互是否正确。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "测试分类体系",
    },
    {
        "title": "关于黑盒测试的常用方法，以下说法正确的是？",
        "description": "关于黑盒测试的常用方法，以下说法正确的是？\n\nA. 等价类划分、边界值分析、因果图、判定表、场景法\nB. 语句覆盖、判定覆盖、条件覆盖\nC. 只有等价类划分\nD. 黑盒测试不需要测试方法",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试分类体系",
    },
    {
        "title": "请判断：系统测试将整个软件系统作为一个整体进行测试，验证其是否满足需求规格。",
        "description": "请判断：系统测试将整个软件系统作为一个整体进行测试，验证其是否满足需求规格。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "测试分类体系",
    },
    {
        "title": "关于静态测试和动态测试的区别，以下说法正确的是？",
        "description": "关于静态测试和动态测试的区别，以下说法正确的是？\n\nA. 静态测试不运行程序，通过审查、走查、静态分析工具进行；动态测试需要运行程序\nB. 静态测试需要运行程序，动态测试不需要\nC. 静态测试和动态测试都需要运行程序\nD. 静态测试和动态测试都不需要运行程序",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试分类体系",
    },
    # ============ 第5节：缺陷管理 (5题) ============
    {
        "title": "缺陷（Bug）的生命周期中，正确的状态流转是？",
        "description": "缺陷（Bug）的生命周期中，正确的状态流转是？\n\nA. New（新建）→ Open（打开/分配）→ Fixed（已修复）→ Verified（已验证）→ Closed（关闭）\nB. New → Closed → Open → Fixed\nC. Open → New → Closed → Fixed\nD. Fixed → New → Open → Closed",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理与追踪",
    },
    {
        "title": "关于缺陷的严重程度（Severity）和优先级（Priority），以下说法正确的是？（多选）",
        "description": "关于缺陷的严重程度（Severity）和优先级（Priority），以下说法正确的是？（多选）\n\nA. 严重程度：Blocker/Critical（致命）→ Major（严重）→ Minor（一般）→ Trivial（轻微）\nB. 优先级：P0-立即 → P1-高 → P2-中\nC. 严重程度和优先级总是相同的\nD. 严重程度和优先级是两个不同的概念",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "缺陷管理与追踪",
    },
    {
        "title": "请判断：当测试人员验证缺陷修复通过后，缺陷状态应该变为「Closed（关闭）」。",
        "description": "请判断：当测试人员验证缺陷修复通过后，缺陷状态应该变为「Closed（关闭）」。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷管理与追踪",
    },
    {
        "title": "关于缺陷状态「Rejected（拒绝/不是bug）」，以下说法正确的是？",
        "description": "关于缺陷状态「Rejected（拒绝/不是bug）」，以下说法正确的是？\n\nA. 开发人员认为提交的不是bug或重复提交，将状态改为Rejected\nB. 测试人员将缺陷状态改为Rejected\nC. Rejected表示缺陷已经修复\nD. Rejected表示缺陷正在修复中",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "缺陷管理与追踪",
    },
    {
        "title": "请判断：缺陷的严重程度（Severity）为Blocker/Critical时，表示系统崩溃、数据丢失等严重问题。",
        "description": "请判断：缺陷的严重程度（Severity）为Blocker/Critical时，表示系统崩溃、数据丢失等严重问题。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "缺陷管理与追踪",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径1的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 1")
    print("🗑️  已删除学习路径1的旧习题")

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
                VALUES (?, ?, ?, ?, ?, 1, ?, 1, ?, datetime('now'), datetime('now'))
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 1", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径1")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 1")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径1现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
