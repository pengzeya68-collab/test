#!/usr/bin/env python3
"""
学习路径6：测试用例设计方法 - 50道精品题
基于测试用例设计的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径6的50道精品题
exercises_data = [
    # ============ 测试用例设计概述（10题）============
    {
        "title": "关于测试用例（Test Case），以下说法正确的是？",
        "description": "关于测试用例（Test Case），以下说法正确的是？\n\nA. 测试用例是一组输入、执行条件和预期结果的集合\nB. 测试用例只需要考虑正常情况\nC. 测试用例设计得越多越好\nD. 测试用例不需要预期结果",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "测试用例设计概述",
    },
    {
        "title": "关于测试用例的要素，以下说法正确的是？（多选）",
        "description": "关于测试用例的要素，以下说法正确的是？（多选）\n\nA. 测试用例编号：唯一标识测试用例\nB. 测试标题：简要描述测试目的\nC. 前置条件：执行测试所需的环境和条件\nD. 预期结果：测试通过后系统应达到的状态",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "测试用例设计概述",
    },
    {
        "title": "请判断：好的测试用例应该尽可能复杂，覆盖多个测试点。",
        "description": "请判断：好的测试用例应该尽可能复杂，覆盖多个测试点。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试用例设计概述",
    },
    {
        "title": "关于测试用例的设计原则，以下说法正确的是？",
        "description": "关于测试用例的设计原则，以下说法正确的是？\n\nA. 测试用例应该具有可重复性\nB. 测试用例应该尽可能复杂\nC. 测试用例不需要考虑边界情况\nD. 测试用例应该依赖特定测试数据",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试用例设计概述",
    },
    {
        "title": "关于测试用例的优先级，以下说法正确的是？（多选）",
        "description": "关于测试用例的优先级，以下说法正确的是？（多选）\n\nA. 高优先级：核心功能、高频使用场景\nB. 中优先级：次要功能、异常场景\nC. 低优先级：边缘情况、很少使用的功能\nD. 优先级只根据功能重要性决定，与风险无关",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试用例设计概述",
    },
    {
        "title": "请判断：测试用例应该做到「去噪」，即排除那些对测试目标没有贡献的步骤。",
        "description": "请判断：测试用例应该做到「去噪」，即排除那些对测试目标没有贡献的步骤。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试用例设计概述",
    },
    {
        "title": "关于测试用例的维护，以下说法正确的是？",
        "description": "关于测试用例的维护，以下说法正确的是？\n\nA. 当需求变更时，需要更新相关的测试用例\nB. 测试用例写好后就不需要再修改\nC. 删除过时的测试用例是不必要的\nD. 测试用例的维护成本很低，可以忽略",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "测试用例设计概述",
    },
    {
        "title": "关于测试用例的评审，以下说法正确的是？（多选）",
        "description": "关于测试用例的评审，以下说法正确的是？（多选）\n\nA. 测试用例评审可以提高测试覆盖率\nB. 评审可以发现测试用例中的错误和遗漏\nC. 评审只需要测试人员参与即可\nD. 评审应该在测试用例执行前进行",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "测试用例设计概述",
    },
    {
        "title": "请判断：测试用例的「预期结果」应该是可以客观判定的。",
        "description": "请判断：测试用例的「预期结果」应该是可以客观判定的。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "测试用例设计概述",
    },
    {
        "title": "关于测试用例的粒度，以下说法正确的是？",
        "description": "关于测试用例的粒度，以下说法正确的是？\n\nA. 测试用例的粒度应该适中，既不要过大也不要过小\nB. 测试用例的粒度越大越好\nC. 测试用例的粒度越小越好\nD. 测试用例的粒度不影响测试效率",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试用例设计概述",
    },
    # ============ 等价类划分（10题）============
    {
        "title": "关于等价类划分，以下说法正确的是？",
        "description": "关于等价类划分，以下说法正确的是？\n\nA. 等价类是指某个输入域的子集中，各个输入数据对于揭露程序中的错误都是等效的\nB. 等价类划分只考虑有效输入\nC. 等价类划分是一种白盒测试技术\nD. 等价类划分不适用于字符型输入",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "等价类划分",
    },
    {
        "title": "关于有效等价类和无效等价类，以下说法正确的是？（多选）",
        "description": "关于有效等价类和无效等价类，以下说法正确的是？（多选）\n\nA. 有效等价类：对于程序规格说明来说，是合理的、有意义的输入数据集合\nB. 无效等价类：对于程序规格说明来说，是不合理的、无意义的输入数据集合\nC. 每个有效等价类都必须设计一个测试用例\nD. 每个无效等价类都必须设计一个测试用例",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "等价类划分",
    },
    {
        "title": "请判断：等价类划分时，应该先划分无效等价类，再划分有效等价类。",
        "description": "请判断：等价类划分时，应该先划分无效等价类，再划分有效等价类。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "等价类划分",
    },
    {
        "title": "某输入框允许输入1-100之间的整数，以下哪些是有效等价类？",
        "description": "某输入框允许输入1-100之间的整数，以下哪些是有效等价类？\n\nA. 1-100之间的任意整数\nB. 小于1的负数\nC. 大于100的正整数\nD. 字母或特殊字符",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "等价类划分",
    },
    {
        "title": "关于等价类划分的原则，以下说法正确的是？（多选）",
        "description": "关于等价类划分的原则，以下说法正确的是？（多选）\n\nA. 如果输入条件规定了取值范围，则可以确定一个有效等价类和两个无效等价类\nB. 如果输入条件规定了输入值的集合，则可以确定一个有效等价类和一个无效等价类\nC. 如果输入条件是一个布尔量，则可以确定一个有效等价类和一个无效等价类\nD. 如果输入条件规定了输入数据的一组值，且程序对不同的输入值做不同的处理，则每个值确定一个有效等价类",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "等价类划分",
    },
    {
        "title": "请判断：在等价类划分中，每个等价类只需要设计一个测试用例即可。",
        "description": "请判断：在等价类划分中，每个等价类只需要设计一个测试用例即可。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "等价类划分",
    },
    {
        "title": "某性别下拉框允许选择「男」或「女」，以下哪些是无效等价类？",
        "description": "某性别下拉框允许选择「男」或「女」，以下哪些是无效等价类？\n\nA. 选择「男」\nB. 选择「女」\nC. 输入「未知」\nD. 留空不选择",
        "solution": "C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "等价类划分",
    },
    {
        "title": "关于等价类划分的优缺点，以下说法正确的是？",
        "description": "关于等价类划分的优缺点，以下说法正确的是？\n\nA. 优点：可以减少测试用例数量，缺点：可能遗漏缺陷\nB. 优点：可以发现的缺陷，缺点：测试用例数量多\nC. 优点：不需要分析需求，缺点：覆盖率低\nD. 优点：适用于所有类型的测试，缺点：执行速度慢",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "等价类划分",
    },
    {
        "title": "请判断：等价类划分不仅适用于输入条件，也适用于输出条件。",
        "description": "请判断：等价类划分不仅适用于输入条件，也适用于输出条件。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "等价类划分",
    },
    {
        "title": "某文件名输入框允许输入1-255个字符的文件名，以下哪些是无效等价类？（多选）",
        "description": "某文件名输入框允许输入1-255个字符的文件名，以下哪些是无效等价类？（多选）\n\nA. 输入0个字符（空文件名）\nB. 输入256个字符\nC. 输入1个字符\nD. 输入255个字符",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "等价类划分",
    },
    # ============ 边界值分析（10题）============
    {
        "title": "关于边界值分析，以下说法正确的是？",
        "description": "关于边界值分析，以下说法正确的是？\n\nA. 边界值分析是对输入或输出的边界值进行测试的一种方法\nB. 边界值分析只适用于数字型输入\nC. 边界值分析是一种白盒测试技术\nD. 边界值分析不需要考虑等价类",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "边界值分析",
    },
    {
        "title": "关于边界值分析的原则，以下说法正确的是？（多选）",
        "description": "关于边界值分析的原则，以下说法正确的是？（多选）\n\nA. 如果输入条件规定了取值范围，则应该测试刚达到这个范围的边界值，以及刚刚超越这个范围边界的值\nB. 通常测试：最小值、最小值+1、正常值、最大值-1、最大值\nC. 边界值分析可以发现的缺陷\nD. 边界值分析只测试输入条件的边界，不测试输出条件的边界",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "边界值分析",
    },
    {
        "title": "请判断：边界值分析是在等价类划分的基础上进行的。",
        "description": "请判断：边界值分析是在等价类划分的基础上进行的。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "边界值分析",
    },
    {
        "title": "某输入框允许输入1-100之间的整数，以下哪些是边界值？（多选）",
        "description": "某输入框允许输入1-100之间的整数，以下哪些是边界值？（多选）\n\nA. 1\nB. 2\nC. 100\nD. 101",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "边界值分析",
    },
    {
        "title": "关于边界值分析和等价类划分的关系，以下说法正确的是？",
        "description": "关于边界值分析和等价类划分的关系，以下说法正确的是？\n\nA. 等价类划分是减少测试用例数量，边界值分析是发现的缺陷\nB. 两种方法独立使用，互不影响\nC. 边界值分析可以替代等价类划分\nD. 等价类划分可以替代边界值分析",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "边界值分析",
    },
    {
        "title": "请判断：边界值分析不仅适用于输入条件，也适用于输出条件。",
        "description": "请判断：边界值分析不仅适用于输入条件，也适用于输出条件。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "边界值分析",
    },
    {
        "title": "某数组可以存储1-100个元素，以下哪些是边界值？（多选）",
        "description": "某数组可以存储1-100个元素，以下哪些是边界值？（多选）\n\nA. 第0个元素（越界）\nB. 第1个元素（边界）\nC. 第100个元素（边界）\nD. 第101个元素（越界）",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "边界值分析",
    },
    {
        "title": "关于健壮边界值分析，以下说法正确的是？",
        "description": "关于健壮边界值分析，以下说法正确的是？\n\nA. 健壮边界值分析会测试：最小值-1、最小值、正常值、最大值、最大值+1\nB. 健壮边界值分析只测试有效边界值\nC. 健壮边界值分析的测试用例数量比普通边界值分析少\nD. 健壮边界值分析不适用于字符型输入",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "边界值分析",
    },
    {
        "title": "请判断：边界值分析可以用于测试用户界面（UI）的边界情况。",
        "description": "请判断：边界值分析可以用于测试用户界面（UI）的边界情况。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "边界值分析",
    },
    {
        "title": "某密码输入框允许输入6-20个字符的密码，以下哪些是边界值？（多选）",
        "description": "某密码输入框允许输入6-20个字符的密码，以下哪些是边界值？（多选）\n\nA. 5个字符\nB. 6个字符\nC. 20个字符\nD. 21个字符",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "边界值分析",
    },
    # ============ 决策表测试（10题）============
    {
        "title": "关于决策表测试，以下说法正确的是？",
        "description": "关于决策表测试，以下说法正确的是？\n\nA. 决策表测试适用于业务逻辑复杂、有多个条件组合的情况\nB. 决策表测试只适用于简单逻辑\nC. 决策表测试是一种白盒测试技术\nD. 决策表测试不需要考虑所有条件组合",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "决策表测试",
    },
    {
        "title": "关于决策表的组成部分，以下说法正确的是？（多选）",
        "description": "关于决策表的组成部分，以下说法正确的是？（多选）\n\nA. 条件桩（Condition Stub）：列出所有条件\nB. 动作桩（Action Stub）：列出所有可能的动作\nC. 条件项（Condition Entry）：给出条件的取值\nD. 动作项（Action Entry）：给出在特定条件组合下应执行的动作",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "决策表测试",
    },
    {
        "title": "请判断：决策表测试可以保证覆盖所有条件组合。",
        "description": "请判断：决策表测试可以保证覆盖所有条件组合。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "决策表测试",
    },
    {
        "title": "关于决策表的化简，以下说法正确的是？",
        "description": "关于决策表的化简，以下说法正确的是？\n\nA. 如果某些条件的变化不影响动作的执行，则可以合并这些规则\nB. 决策表不应该化简，应该保留所有规则\nC. 化简会导致测试覆盖率降低\nD. 只有完全相同的规则才能合并",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "决策表测试",
    },
    {
        "title": "关于决策表的适用场景，以下说法正确的是？（多选）",
        "description": "关于决策表的适用场景，以下说法正确的是？（多选）\n\nA. 适用于有多个条件且条件之间存在复杂组合关系的情况\nB. 适用于业务规则明确、可以用条件判断来描述的情况\nC. 适用于输入域很大的情况\nD. 适用于探索性测试",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "决策表测试",
    },
    {
        "title": "请判断：决策表测试是一种黑盒测试技术。",
        "description": "请判断：决策表测试是一种黑盒测试技术。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "决策表测试",
    },
    {
        "title": "某系统根据用户类型和订单金额决定折扣，以下哪些是决策表的条件？（多选）",
        "description": "某系统根据用户类型和订单金额决定折扣，以下哪些是决策表的条件？（多选）\n\nA. 用户类型（普通用户/VIP用户）\nB. 订单金额（<100元/100-500元/>500元）\nC. 折扣比例（0%/5%/10%）\nD. 支付方式（支付宝/微信/银行卡）",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "决策表测试",
    },
    {
        "title": "关于决策表的优点，以下说法正确的是？",
        "description": "关于决策表的优点，以下说法正确的是？\n\nA. 可以清晰地表示复杂业务逻辑，确保不遗漏任何条件组合\nB. 可以减少测试用例数量\nC. 不需要分析需求就可以创建决策表\nD. 执行速度比等价类划分快",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "决策表测试",
    },
    {
        "title": "请判断：如果条件数量很多，决策表的规则数会呈指数增长，这时可以使用决策表化简技术。",
        "description": "请判断：如果条件数量很多，决策表的规则数会呈指数增长，这时可以使用决策表化简技术。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "决策表测试",
    },
    {
        "title": "关于决策表和因果图的关系，以下说法正确的是？（多选）",
        "description": "关于决策表和因果图的关系，以下说法正确的是？（多选）\n\nA. 因果图是一种生成决策表的辅助工具\nB. 因果图可以帮助识别条件之间的约束关系\nC. 决策表可以直接从需求说明中创建，不一定需要因果图\nD. 因果图适用于条件数量很多的情况",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "决策表测试",
    },
    # ============ 正交实验设计（10题）============
    {
        "title": "关于正交实验设计（Orthogonal Experimental Design），以下说法正确的是？",
        "description": "关于正交实验设计（Orthogonal Experimental Design），以下说法正确的是？\n\nA. 正交实验设计可以在保证一定覆盖率的前提下，大幅减少测试用例数量\nB. 正交实验设计需要测试所有条件组合\nC. 正交实验设计是一种白盒测试技术\nD. 正交实验设计不适用于多因素多水平的实验",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "关于正交表的特性，以下说法正确的是？（多选）",
        "description": "关于正交表的特性，以下说法正确的是？（多选）\n\nA. 每列中各个数字（水平）出现的次数相同（均衡分散性）\nB. 任意两列中，各种可能的数字对（水平对）出现的次数相同（整齐可比性）\nC. 正交表可以保证覆盖所有条件组合\nD. 正交表是一种随机生成的表",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "请判断：正交实验设计适用于因素（条件）数量多、每个因素的水平也多的情况。",
        "description": "请判断：正交实验设计适用于因素（条件）数量多、每个因素的水平也多的情况。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "某系统有3个因素，每个因素有3个水平，如果全组合测试需要多少个测试用例？",
        "description": "某系统有3个因素，每个因素有3个水平，如果全组合测试需要多少个测试用例？\n\nA. 3个\nB. 9个\nC. 27个\nD. 81个",
        "solution": "C",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "正交实验设计",
    },
    {
        "title": "关于正交实验设计的优缺点，以下说法正确的是？（多选）",
        "description": "关于正交实验设计的优缺点，以下说法正确的是？（多选）\n\nA. 优点：可以在保证一定覆盖率的前提下，大幅减少测试用例数量\nB. 优点：可以发现的缺陷\nC. 缺点：可能会遗漏某些重要的条件组合\nD. 缺点：不适用于软件测试",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "请判断：正交实验设计是一种部分因子实验设计方法。",
        "description": "请判断：正交实验设计是一种部分因子实验设计方法。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "关于正交表的表示法 L_9(3^4)，以下说法正确的是？",
        "description": "关于正交表的表示法 L_9(3^4)，以下说法正确的是？\n\nA. 表示需要做9次实验，每个因素有3个水平，最多可安排4个因素\nB. 表示需要做3次实验，每个因素有9个水平，最多可安排4个因素\nC. 表示需要做9次实验，每个因素有4个水平，最多可安排3个因素\nD. 表示需要做4次实验，每个因素有9个水平，最多可安排3个因素",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "关于正交实验设计的选择原则，以下说法正确的是？（多选）",
        "description": "关于正交实验设计的选择原则，以下说法正确的是？（多选）\n\nA. 如果因素的水平数相同，选择正交表时应该让因素数小于或等于正交表的列数\nB. 如果没有合适的正交表，可以选择稍大一些的正交表，将多余列空着不安排因素\nC. 应该选择最小的正交表，以最大限度减少测试用例数量\nD. 正交表的选择不影响测试覆盖率",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "请判断：正交实验设计可以保证两两因素之间的所有水平组合都被覆盖到。",
        "description": "请判断：正交实验设计可以保证两两因素之间的所有水平组合都被覆盖到。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
    {
        "title": "关于正交实验设计在软件测试中的应用，以下说法正确的是？（多选）",
        "description": "关于正交实验设计在软件测试中的应用，以下说法正确的是？（多选）\n\nA. 适用于配置测试（不同操作系统、浏览器、分辨率的组合）\nB. 适用于兼容性测试\nC. 适用于单元测试\nD. 适用于探索性测试",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "正交实验设计",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径6的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 6")
    print("🗑️  已删除学习路径6（测试用例设计方法）的旧习题")

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
                VALUES (?, ?, ?, ?, ?, 6, ?, 1, ?, datetime('now'), datetime('now'))
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 6", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径6（测试用例设计方法）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 6")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径6现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
