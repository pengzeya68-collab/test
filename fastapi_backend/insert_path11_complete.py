#!/usr/bin/env python3
"""
学习路径11：接口自动化测试 - Requests+Pytest - 50道精品题（完整版）
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

exercises_data = [
    # ============ Requests库基础（10题）============
    {
        "title": "关于Python的Requests库，以下说法正确的是？",
        "description": "关于Python的Requests库，以下说法正确的是？\n\nA. Requests是一个简洁易用的HTTP库\nB. Requests只能用于测试\nC. Requests是Python内置库\nD. Requests不支持HTTPS",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "Requests库基础",
    },
    {
        "title": "关于requests.get()方法，以下说法正确的是？（多选）",
        "description": "关于requests.get()方法，以下说法正确的是？（多选）\n\nA. 用于发送GET请求\nB. 可以传递params参数\nC. 可以传递headers参数\nD. get()方法只能用于HTTP",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Requests库基础",
    },
    {
        "title": "请判断：requests.post()方法用于发送POST请求。",
        "description": "请判断：requests.post()方法用于发送POST请求。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Requests库基础",
    },
    {
        "title": "关于Response对象，以下说法正确的是？",
        "description": "关于Response对象，以下说法正确的是？\n\nA. 包含状态码、响应头、响应体\nB. 只包含状态码\nC. 不包含响应体\nD. 无法获取响应头",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Requests库基础",
    },
    {
        "title": "关于requests的请求参数，以下说法正确的是？（多选）",
        "description": "关于requests的请求参数，以下说法正确的是？（多选）\n\nA. params用于URL查询参数\nB. data用于表单数据\nC. json用于JSON数据\nD. headers用于请求头",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Requests库基础",
    },
    {
        "title": "请判断：response.json()方法用于解析JSON响应体。",
        "description": "请判断：response.json()方法用于解析JSON响应体。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Requests库基础",
    },
    {
        "title": "关于requests的超时设置，以下说法正确的是？",
        "description": "关于requests的超时设置，以下说法正确的是？\n\nA. 可以使用timeout参数\nB. requests默认有超时限制\nC. 超时设置不重要\nD. 超时只适用于POST",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Requests库基础",
    },
    {
        "title": "关于requests的异常处理，以下说法正确的是？（多选）",
        "description": "关于requests的异常处理，以下说法正确的是？（多选）\n\nA. 可能抛出RequestException\nB. 超时会抛出Timeout\nC. 连接错误会抛出ConnectionError\nD. requests不会抛异常",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Requests库基础",
    },
    {
        "title": "请判断：requests.Session()可以跨请求保持Cookie。",
        "description": "请判断：requests.Session()可以跨请求保持Cookie。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "Requests库基础",
    },
    {
        "title": "关于requests的SSL验证，以下说法正确的是？",
        "description": "关于requests的SSL验证，以下说法正确的是？\n\nA. 可以设置verify=False跳过验证\nB. SSL验证不能跳过\nC. SSL验证只适用于HTTPS\nD. SSL验证默认关闭",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Requests库基础",
    },
    # ============ Pytest框架基础（10题）============
    {
        "title": "关于Pytest框架，以下说法正确的是？",
        "description": "关于Pytest框架，以下说法正确的是？\n\nA. Pytest是功能强大的Python测试框架\nB. Pytest只支持单元测试\nC. Pytest不支持插件\nD. Pytest是内置库",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "Pytest框架基础",
    },
    {
        "title": "关于Pytest的用例发现，以下说法正确的是？（多选）",
        "description": "关于Pytest的用例发现，以下说法正确的是？（多选）\n\nA. 测试文件以test_开头\nB. 测试函数以test_开头\nC. 测试类以Test开头\nD. Pytest不能自动发现",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Pytest框架基础",
    },
    {
        "title": "请判断：Pytest支持参数化测试。",
        "description": "请判断：Pytest支持参数化测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Pytest框架基础",
    },
    {
        "title": "关于Pytest的Fixture，以下说法正确的是？",
        "description": "关于Pytest的Fixture，以下说法正确的是？\n\nA. 用于提供测试前置和后置\nB. Fixture没有用\nC. Fixture只能用于单个函数\nD. Fixture不支持参数化",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础",
    },
    {
        "title": "关于Pytest的断言，以下说法正确的是？（多选）",
        "description": "关于Pytest的断言，以下说法正确的是？（多选）\n\nA. 可以使用assert语句\nB. 断言失败会显示详细信息\nC. 可以使用pytest.raises()\nD. Pytest不支持断言",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Pytest框架基础",
    },
    {
        "title": "请判断：Pytest可以生成HTML测试报告。",
        "description": "请判断：Pytest可以生成HTML测试报告。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Pytest框架基础",
    },
    {
        "title": "关于Pytest的标记，以下说法正确的是？",
        "description": "关于Pytest的标记，以下说法正确的是？\n\nA. 可以使用@pytest.mark标记\nB. 标记没有用\nC. 标记只能在命令行使用\nD. Pytest不支持标记",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础",
    },
    {
        "title": "关于Pytest的配置文件，以下说法正确的是？（多选）",
        "description": "关于Pytest的配置文件，以下说法正确的是？（多选）\n\nA. 可以使用pytest.ini\nB. 可以配置测试路径\nC. 配置文件是必需的\nD. 配置文件不支持自定义标记",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础",
    },
    {
        "title": "请判断：Pytest支持并行执行测试。",
        "description": "请判断：Pytest支持并行执行测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "Pytest框架基础",
    },
    {
        "title": "关于Pytest的用例执行顺序，以下说法正确的是？",
        "description": "关于Pytest的用例执行顺序，以下说法正确的是？\n\nA. 默认按文件内容和函数名排序\nB. Pytest会随机执行\nC. Pytest按编写顺序执行\nD. Pytest不支持控制顺序",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础",
    },
    # ============ 接口自动化测试实战（15题）============
    {
        "title": "关于接口自动化测试的框架搭建，以下说法正确的是？",
        "description": "关于接口自动化测试的框架搭建，以下说法正确的是？\n\nA. 应该分层设计\nB. 所有代码写在一个文件\nC. 不需要框架\nD. 框架越复杂越好",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试用例的组织，以下说法正确的是？（多选）",
        "description": "关于接口测试用例的组织，以下说法正确的是？（多选）\n\nA. 应该按模块组织\nB. 应该使用配置文件\nC. 应该提取公共操作\nD. 所有用例写一个文件",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "请判断：接口自动化测试应该验证状态码和响应体。",
        "description": "请判断：接口自动化测试应该验证状态码和响应体。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口依赖处理，以下说法正确的是？",
        "description": "关于接口依赖处理，以下说法正确的是？\n\nA. 应该在一个用例中完成依赖\nB. 接口之间没有依赖\nC. 依赖处理很复杂\nD. 依赖只能手动处理",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于测试数据的管理，以下说法正确的是？（多选）",
        "description": "关于测试数据的管理，以下说法正确的是？（多选）\n\nA. 应该使用独立的数据文件\nB. 可以使用Fixture准备数据\nC. 应该保证独立性\nD. 数据硬编码在脚本中",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "请判断：接口自动化测试应该生成详细的测试报告。",
        "description": "请判断：接口自动化测试应该生成详细的测试报告。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试的断言设计，以下说法正确的是？",
        "description": "关于接口测试的断言设计，以下说法正确的是？\n\nA. 应该断言状态码和关键字段\nB. 只需要断言状态码\nC. 断言越多越好\nD. 不需要断言",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试的日志，以下说法正确的是？（多选）",
        "description": "关于接口测试的日志，以下说法正确的是？（多选）\n\nA. 应该记录请求响应\nB. 日志应便于调试\nC. 可以使用logging模块\nD. 日志不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "请判断：接口自动化测试应该与CI/CD集成。",
        "description": "请判断：接口自动化测试应该与CI/CD集成。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试的异常处理，以下说法正确的是？",
        "description": "关于接口测试的异常处理，以下说法正确的是？\n\nA. 应该捕获并记录异常\nB. 异常不需要处理\nC. 异常导致中断\nD. 异常处理很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试的执行策略，以下说法正确的是？（多选）",
        "description": "关于接口测试的执行策略，以下说法正确的是？（多选）\n\nA. 应该支持按模块执行\nB. 应该支持失败重试\nC. 应该快速反馈\nD. 所有测试必须一次执行",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "请判断：接口自动化测试应该定期执行。",
        "description": "请判断：接口自动化测试应该定期执行。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试的报告内容，以下说法正确的是？",
        "description": "关于接口测试的报告内容，以下说法正确的是？\n\nA. 应包括执行结果和错误信息\nB. 只需要显示通过率\nC. 报告越简单越好\nD. 报告不需要详细信息",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "关于接口测试的维护，以下说法正确的是？（多选）",
        "description": "关于接口测试的维护，以下说法正确的是？（多选）\n\nA. 接口变更应及时更新\nB. 应定期回顾用例\nC. 应提高可维护性\nD. 脚本写好就不需要维护",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战",
    },
    {
        "title": "请判断：接口自动化测试可以提高效率但不能替代手工测试。",
        "description": "请判断：接口自动化测试可以提高效率但不能替代手工测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战",
    },
    # ============ 高级话题（15题）============
    {
        "title": "关于接口mock，以下说法正确的是？",
        "description": "关于接口mock，以下说法正确的是？\n\nA. Mock可以模拟未完成的接口\nB. Mock没有用\nC. Mock只能用于单元测试\nD. Mock很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "请判断：可以使用requests-mock库模拟HTTP请求。",
        "description": "请判断：可以使用requests-mock库模拟HTTP请求。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口自动化测试的数据驱动，以下说法正确的是？（多选）",
        "description": "关于接口自动化测试的数据驱动，以下说法正确的是？（多选）\n\nA. 可以使用Excel/CSV/JSON存储数据\nB. 可以使用parametrize实现\nC. 数据驱动可以提高覆盖率\nD. 数据驱动没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "请判断：接口自动化测试应该包含安全性测试。",
        "description": "请判断：接口自动化测试应该包含安全性测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口测试的并发处理，以下说法正确的是？",
        "description": "关于接口测试的并发处理，以下说法正确的是？\n\nA. 可以使用多线程实现并发\nB. 并发测试没有用\nC. 并发只适用于性能测试\nD. 并发很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口测试的环境管理，以下说法正确的是？（多选）",
        "description": "关于接口测试的环境管理，以下说法正确的是？（多选）\n\nA. 应该使用配置文件管理地址\nB. 可以使用环境变量\nC. 应避免硬编码\nD. 环境管理不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "请判断：接口自动化测试应该生成Allure报告。",
        "description": "请判断：接口自动化测试应该生成Allure报告。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口测试的重试机制，以下说法正确的是？",
        "description": "关于接口测试的重试机制，以下说法正确的是？\n\nA. 可以使用flaky插件实现\nB. 重试机制没有用\nC. 重试会导致不稳定\nD. 重试很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口性能测试，以下说法正确的是？（多选）",
        "description": "关于接口性能测试，以下说法正确的是？（多选）\n\nA. 可以使用Locust、JMeter\nB. 应测试响应时间和吞吐量\nC. 性能测试很重要\nD. 性能测试不需要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "请判断：接口自动化测试应该支持多环境配置。",
        "description": "请判断：接口自动化测试应该支持多环境配置。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口测试的持续集成，以下说法正确的是？",
        "description": "关于接口测试的持续集成，以下说法正确的是？\n\nA. 可以集成到Jenkins、GitLab CI\nB. 持续集成不重要\nC. 持续集成很复杂\nD. 不需要持续集成",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口测试的最佳实践，以下说法正确的是？（多选）",
        "description": "关于接口测试的最佳实践，以下说法正确的是？（多选）\n\nA. 应遵循独立性原则\nB. 应快速反馈\nC. 应易于维护\nD. 最佳实践不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "请判断：接口自动化测试应该包含回归测试。",
        "description": "请判断：接口自动化测试应该包含回归测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "关于接口测试的未来发展，以下说法正确的是？（多选）",
        "description": "关于接口测试的未来发展，以下说法正确的是？（多选）\n\nA. AI辅助生成用例\nB. 更多云原生支持\nC. 智能缺陷定位\nD. 接口测试会被淘汰",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题",
    },
    {
        "title": "请判断：接口自动化测试是敏捷开发的重要支撑。",
        "description": "请判断：接口自动化测试是敏捷开发的重要支撑。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "高级话题",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 11")
    print("🗑️  已删除学习路径11的旧习题")
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"
            cursor.execute(
                """INSERT INTO exercises (title, description, solution, exercise_type, difficulty, learning_path_id, category, is_public, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 11, ?, 1, ?, datetime('now'), datetime('now'))""",
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 11", (inserted,))
    conn.commit()
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径11")
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 11")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径11现在有 {count} 道习题")
    conn.close()


if __name__ == "__main__":
    main()
