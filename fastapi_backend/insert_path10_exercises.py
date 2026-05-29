#!/usr/bin/env python3
"""
学习路径10：UI自动化测试 - Selenium - 50道精品题
基于UI自动化测试与Selenium的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径10的50道精品题
exercises_data = [
    # ============ Selenium概述（10题）============
    {
        "title": "关于Selenium，以下说法正确的是？",
        "description": "关于Selenium，以下说法正确的是？\n\nA. Selenium是一个用于Web应用UI自动化测试的工具\nB. Selenium只能用于手工测试\nC. Selenium不支持跨浏览器测试\nD. Selenium是商业工具",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "Selenium概述",
    },
    {
        "title": "关于Selenium的组件，以下说法正确的是？（多选）",
        "description": "关于Selenium的组件，以下说法正确的是？（多选）\n\nA. Selenium WebDriver用于编写测试脚本\nB. Selenium IDE用于录制和回放测试\nC. Selenium Grid用于并行执行测试\nD. Selenium只有一个组件",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Selenium概述",
    },
    {
        "title": "请判断：Selenium支持多种编程语言（如：Java、Python、C#）。",
        "description": "请判断：Selenium支持多种编程语言（如：Java、Python、C#）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Selenium概述",
    },
    {
        "title": "关于Selenium WebDriver的工作原理，以下说法正确的是？",
        "description": "关于Selenium WebDriver的工作原理，以下说法正确的是？\n\nA. WebDriver通过浏览器驱动程序与浏览器通信\nB. WebDriver直接操作浏览器\nC. WebDriver只支持Chrome浏览器\nD. WebDriver不需要浏览器驱动",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Selenium概述",
    },
    {
        "title": "关于Selenium与其他自动化工具的比较，以下说法正确的是？（多选）",
        "description": "关于Selenium与其他自动化工具的比较，以下说法正确的是？（多选）\n\nA. Selenium是开源免费的\nB. Selenium支持跨浏览器测试\nC. Selenium支持多种编程语言\nD. Selenium比所有商业工具都差",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Selenium概述",
    },
    {
        "title": "请判断：Selenium可以测试桌面应用。",
        "description": "请判断：Selenium可以测试桌面应用。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Selenium概述",
    },
    {
        "title": "关于Selenium的安装，以下说法正确的是？",
        "description": "关于Selenium的安装，以下说法正确的是？\n\nA. 需要安装浏览器驱动程序（如：ChromeDriver）\nB. 只需要安装Selenium库即可\nC. 不需要安装任何东西\nD. 必须使用IDE",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Selenium概述",
    },
    {
        "title": "关于Selenium的应用场景，以下说法正确的是？（多选）",
        "description": "关于Selenium的应用场景，以下说法正确的是？（多选）\n\nA. 适用于回归测试\nB. 适用于跨浏览器测试\nC. 适用于性能测试\nD. 适用于UI功能测试",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Selenium概述",
    },
    {
        "title": "请判断：Selenium支持移动端应用测试。",
        "description": "请判断：Selenium支持移动端应用测试。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Selenium概述",
    },
    {
        "title": "关于Selenium 3与Selenium 4的区别，以下说法正确的是？",
        "description": "关于Selenium 3与Selenium 4的区别，以下说法正确的是？\n\nA. Selenium 4支持相对定位器、新的窗口管理API\nB. Selenium 3比Selenium 4更强大\nC. Selenium 4不支持Chrome浏览器\nD. Selenium 3和Selenium 4完全相同",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Selenium概述",
    },
    # ============ 元素定位（10题）============
    {
        "title": "关于Selenium的元素定位，以下说法正确的是？",
        "description": "关于Selenium的元素定位，以下说法正确的是？\n\nA. 可以通过ID、Name、Class、XPath、CSS Selector等方式定位元素\nB. 元素定位只有一种方式\nC. 元素定位不重要\nD. 元素定位只使用ID",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "元素定位",
    },
    {
        "title": "关于XPath定位，以下说法正确的是？（多选）",
        "description": "关于XPath定位，以下说法正确的是？（多选）\n\nA. XPath可以通过绝对路径定位\nB. XPath可以通过相对路径定位\nC. XPath支持使用文本内容定位\nD. XPath只支持绝对路径",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "元素定位",
    },
    {
        "title": "请判断：CSS Selector通常比XPath更快。",
        "description": "请判断：CSS Selector通常比XPath更快。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "元素定位",
    },
    {
        "title": "关于ID定位，以下说法正确的是？",
        "description": "关于ID定位，以下说法正确的是？\n\nA. ID应该是唯一的，是最优先的定位方式\nB. ID可以重复\nC. ID定位不可靠\nD. ID定位速度最慢",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "元素定位",
    },
    {
        "title": "关于元素定位的最佳实践，以下说法正确的是？（多选）",
        "description": "关于元素定位的最佳实践，以下说法正确的是？（多选）\n\nA. 优先使用ID、Name等稳定属性\nB. 避免使用动态变化的属性\nC. 使用相对路径而非绝对路径\nD. 随意选择定位方式",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "元素定位",
    },
    {
        "title": "请判断：如果元素没有ID，可以使用Name或Class属性定位。",
        "description": "请判断：如果元素没有ID，可以使用Name或Class属性定位。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "元素定位",
    },
    {
        "title": "关于XPath的轴（Axes），以下说法正确的是？",
        "description": "关于XPath的轴（Axes），以下说法正确的是？\n\nA. 可以通过父子、兄弟关系定位元素\nB. XPath的轴没有用\nC. XPath的轴只用于文本定位\nD. XPath不支持轴",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "元素定位",
    },
    {
        "title": "关于元素定位的调试，以下说法正确的是？（多选）",
        "description": "关于元素定位的调试，以下说法正确的是？（多选）\n\nA. 可以使用浏览器开发者工具验证定位表达式\nB. 可以使用Selenium IDE录制获取定位\nC. 应该定期检查元素定位是否仍然有效\nD. 元素定位不需要调试",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "元素定位",
    },
    {
        "title": "请判断：CSS Selector支持通过文本内容定位元素。",
        "description": "请判断：CSS Selector支持通过文本内容定位元素。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "元素定位",
    },
    {
        "title": "关于动态元素的定位，以下说法正确的是？",
        "description": "关于动态元素的定位，以下说法正确的是？\n\nA. 可以使用contains()、starts-with()等函数\nB. 动态元素无法定位\nC. 动态元素只使用ID定位\nD. 动态元素不需要特殊处理",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "元素定位",
    },
    # ============ 常用操作（10题）============
    {
        "title": "关于Selenium的常用操作，以下说法正确的是？",
        "description": "关于Selenium的常用操作，以下说法正确的是？\n\nA. 包括：点击、输入文本、清除文本、获取文本\nB. Selenium只能点击元素\nC. Selenium不能输入文本\nD. Selenium的操作很少",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "常用操作",
    },
    {
        "title": "关于元素的点击操作，以下说法正确的是？（多选）",
        "description": "关于元素的点击操作，以下说法正确的是？（多选）\n\nA. 可以使用click()方法\nB. 应该确保元素可见且可点击\nC. 可以使用JavaScript强制点击\nD. 点击操作一定会成功",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "常用操作",
    },
    {
        "title": "请判断：send_keys()方法用于向输入框输入文本。",
        "description": "请判断：send_keys()方法用于向输入框输入文本。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "常用操作",
    },
    {
        "title": "关于获取元素文本，以下说法正确的是？",
        "description": "关于获取元素文本，以下说法正确的是？\n\nA. 可以使用text属性或get_attribute('value')\nB. 获取文本只有一种方式\nC. 无法获取元素文本\nD. 获取文本很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "常用操作",
    },
    {
        "title": "关于下拉框操作，以下说法正确的是？（多选）",
        "description": "关于下拉框操作，以下说法正确的是？（多选）\n\nA. 可以使用Select类\nB. 可以通过index、value、visible text选择选项\nC. 可以获取所有可选选项\nD. 下拉框无法自动化操作",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "常用操作",
    },
    {
        "title": "请判断：clear()方法用于清除输入框的文本。",
        "description": "请判断：clear()方法用于清除输入框的文本。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "常用操作",
    },
    {
        "title": "关于弹窗处理，以下说法正确的是？",
        "description": "关于弹窗处理，以下说法正确的是？\n\nA. 可以使用switch_to.alert切换到弹窗\nB. 弹窗无法处理\nC. 弹窗只有关闭操作\nD. 弹窗处理很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "常用操作",
    },
    {
        "title": "关于多窗口/多标签页处理，以下说法正确的是？（多选）",
        "description": "关于多窗口/多标签页处理，以下说法正确的是？（多选）\n\nA. 可以使用window_handles获取所有窗口句柄\nB. 可以使用switch_to.window()切换窗口\nC. 应该关闭不需要的窗口\nD. 多窗口无法处理",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "常用操作",
    },
    {
        "title": "请判断：Selenium可以操作文件上传。",
        "description": "请判断：Selenium可以操作文件上传。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "常用操作",
    },
    {
        "title": "关于鼠标悬停操作，以下说法正确的是？",
        "description": "关于鼠标悬停操作，以下说法正确的是？\n\nA. 可以使用ActionChains类\nB. 鼠标悬停无法自动化\nC. 鼠标悬停只使用click()\nD. 鼠标操作很有限",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "常用操作",
    },
    # ============ 等待机制（10题）============
    {
        "title": "关于Selenium的等待机制，以下说法正确的是？",
        "description": "关于Selenium的等待机制，以下说法正确的是？\n\nA. 包括：强制等待、隐式等待、显式等待\nB. 等待机制只有一种\nC. 不需要等待机制\nD. 等待机制不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "等待机制",
    },
    {
        "title": "关于强制等待（time.sleep），以下说法正确的是？（多选）",
        "description": "关于强制等待（time.sleep），以下说法正确的是？（多选）\n\nA. 会固定等待指定时间\nB. 不推荐在生产代码中使用\nC. 可以用于调试\nD. 强制等待是最好的等待方式",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "等待机制",
    },
    {
        "title": "请判断：隐式等待（implicitly_wait）会应用于所有元素查找。",
        "description": "请判断：隐式等待（implicitly_wait）会应用于所有元素查找。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "等待机制",
    },
    {
        "title": "关于显式等待（WebDriverWait），以下说法正确的是？",
        "description": "关于显式等待（WebDriverWait），以下说法正确的是？\n\nA. 可以等待特定条件满足后再执行后续操作\nB. 显式等待会一直等待\nC. 显式等待不灵活\nD. 显式等待不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "等待机制",
    },
    {
        "title": "关于等待机制的最佳实践，以下说法正确的是？（多选）",
        "description": "关于等待机制的最佳实践，以下说法正确的是？（多选）\n\nA. 优先使用显式等待\nB. 避免使用强制等待\nC. 合理设置等待超时时间\nD. 不需要等待机制",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "等待机制",
    },
    {
        "title": "请判断：expected_conditions模块提供了常用的等待条件。",
        "description": "请判断：expected_conditions模块提供了常用的等待条件。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "等待机制",
    },
    {
        "title": "关于FluientWait，以下说法正确的是？",
        "description": "关于FluientWait，以下说法正确的是？\n\nA. 可以更灵活地控制等待频率和忽略特定异常\nB. FluientWait没有用\nC. FluientWait只用于Python\nD. FluientWait不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "等待机制",
    },
    {
        "title": "关于页面加载等待，以下说法正确的是？（多选）",
        "description": "关于页面加载等待，以下说法正确的是？（多选）\n\nA. 可以设置页面加载超时时间\nB. 可以使用JavaScript判断页面是否加载完成\nC. 应该等待页面完全加载后再操作元素\nD. 页面加载不需要等待",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "等待机制",
    },
    {
        "title": "请判断：等待机制可以提高测试脚本的稳定性。",
        "description": "请判断：等待机制可以提高测试脚本的稳定性。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "等待机制",
    },
    {
        "title": "关于等待机制的调试，以下说法正确的是？",
        "description": "关于等待机制的调试，以下说法正确的是？\n\nA. 应该记录等待超时时的页面状态\nB. 等待机制不需要调试\nC. 等待超时无法调试\nD. 调试等待机制很困难",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "等待机制",
    },
    # ============ 测试框架集成（10题）============
    {
        "title": "关于Selenium与测试框架的集成，以下说法正确的是？",
        "description": "关于Selenium与测试框架的集成，以下说法正确的是？\n\nA. Selenium可以与Pytest、unittest、TestNG等框架集成\nB. Selenium不能与其他框架集成\nC. Selenium只能单独使用\nD. 集成很困难",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试框架集成",
    },
    {
        "title": "关于Selenium与Pytest的集成，以下说法正确的是？（多选）",
        "description": "关于Selenium与Pytest的集成，以下说法正确的是？（多选）\n\nA. 可以使用fixture管理浏览器生命周期\nB. 可以使用parametrize实现数据驱动\nC. 可以使用pytest-html生成测试报告\nD. Selenium与Pytest不能集成",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
    {
        "title": "请判断：Selenium测试脚本应该遵循Page Object模式。",
        "description": "请判断：Selenium测试脚本应该遵循Page Object模式。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
    {
        "title": "关于测试报告，以下说法正确的是？",
        "description": "关于测试报告，以下说法正确的是？\n\nA. 可以使用Allure、pytest-html等生成测试报告\nB. 测试报告不重要\nC. 测试报告只显示通过率\nD. 测试报告很难生成",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "测试框架集成",
    },
    {
        "title": "关于持续集成，以下说法正确的是？（多选）",
        "description": "关于持续集成，以下说法正确的是？（多选）\n\nA. Selenium测试可以集成到Jenkins、GitLab CI等CI/CD工具\nB. 应该自动化执行测试并反馈结果\nC. 持续集成可以提高测试效率\nD. 持续集成不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
    {
        "title": "请判断：Selenium测试脚本应该包含断言（Assertion）。",
        "description": "请判断：Selenium测试脚本应该包含断言（Assertion）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "测试框架集成",
    },
    {
        "title": "关于测试数据管理，以下说法正确的是？",
        "description": "关于测试数据管理，以下说法正确的是？\n\nA. 应该使用独立的测试数据文件或数据库\nB. 测试数据不需要管理\nC. 测试数据可以硬编码在脚本中\nD. 测试数据管理很困难",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
    {
        "title": "关于并行执行，以下说法正确的是？（多选）",
        "description": "关于并行执行，以下说法正确的是？（多选）\n\nA. 可以使用Selenium Grid或pytest-xdist实现并行执行\nB. 并行执行可以提高测试速度\nC. 并行执行需要管理测试依赖\nD. 并行执行没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
    {
        "title": "请判断：Selenium 4支持相对定位器（Relative Locators）。",
        "description": "请判断：Selenium 4支持相对定位器（Relative Locators）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
    {
        "title": "关于Selenium的最佳实践，以下说法正确的是？",
        "description": "关于Selenium的最佳实践，以下说法正确的是？\n\nA. 应该遵循：元素定位与测试逻辑分离、使用配置文件、定期维护脚本\nB. 最佳实践不重要\nC. 最佳实践很复杂\nD. 不需要最佳实践",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试框架集成",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径10的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 10")
    print("🗑️  已删除学习路径10（UI自动化测试 - Selenium）的旧习题")

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
                VALUES (?, ?, ?, ?, ?, 10, ?, 1, ?, datetime('now'), datetime('now'))
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 10", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径10（UI自动化测试 - Selenium）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 10")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径10现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
