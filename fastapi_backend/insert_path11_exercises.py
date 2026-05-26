#!/usr/bin/env python3
"""
学习路径11：接口自动化测试 - Requests+Pytest - 50道精品题
基于接口自动化测试的真实课程内容出题
"""

import sqlite3

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'

# 学习路径11的50道精品题
exercises_data = [
    # ============ Requests库基础（10题）============
    {
        "title": "关于Python的Requests库，以下说法正确的是？",
        "description": "关于Python的Requests库，以下说法正确的是？\n\nA. Requests是一个简洁易用的HTTP库，用于发送HTTP请求\nB. Requests只能用于测试\nC. Requests是Python内置库\nD. Requests不支持HTTPS",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "Requests库基础"
    },
    {
        "title": "关于requests.get()方法，以下说法正确的是？（多选）",
        "description": "关于requests.get()方法，以下说法正确的是？（多选）\n\nA. 用于发送GET请求\nB. 可以传递params参数\nC. 可以传递headers参数\nD. get()方法只能用于HTTP，不能用于HTTPS",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Requests库基础"
    },
    {
        "title": "请判断：requests.post()方法用于发送POST请求。",
        "description": "请判断：requests.post()方法用于发送POST请求。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Requests库基础"
    },
    {
        "title": "关于Response对象，以下说法正确的是？",
        "description": "关于Response对象，以下说法正确的是？\n\nA. 包含状态码、响应头、响应体等信息\nB. Response对象只包含状态码\nC. Response对象不包含响应体\nD. Response对象无法获取响应头",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Requests库基础"
    },
    {
        "title": "关于requests的请求参数，以下说法正确的是？（多选）",
        "description": "关于requests的请求参数，以下说法正确的是？（多选）\n\nA. params用于URL查询参数\nB. data用于表单数据\nC. json用于JSON数据\nD. headers用于请求头",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Requests库基础"
    },
    {
        "title": "请判断：response.json()方法用于解析JSON响应体。",
        "description": "请判断：response.json()方法用于解析JSON响应体。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Requests库基础"
    },
    {
        "title": "关于requests的超时设置，以下说法正确的是？",
        "description": "关于requests的超时设置，以下说法正确的是？\n\nA. 可以使用timeout参数设置超时时间\nB. requests默认有超时限制\nC. 超时设置不重要\nD. 超时设置只适用于POST请求",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Requests库基础"
    },
    {
        "title": "关于requests的异常处理，以下说法正确的是？（多选）",
        "description": "关于requests的异常处理，以下说法正确的是？（多选）\n\nA. 可能抛出requests.exceptions.RequestException\nB. 超时会抛出Timeout异常\nC. 连接错误会抛出ConnectionError异常\nD. requests不会抛出异常",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Requests库基础"
    },
    {
        "title": "请判断：requests可以同时处理多个请求（并发）。",
        "description": "请判断：requests可以同时处理多个请求（并发）。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "Requests库基础"
    },
    {
        "title": "关于requests.Session()，以下说法正确的是？",
        "description": "关于requests.Session()，以下说法正确的是？\n\nA. Session可以跨请求保持Cookie和头部信息\nB. Session没有用\nC. Session只能用于单个请求\nD. Session不支持连接池",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Requests库基础"
    },
    
    # ============ Pytest框架基础（10题）============
    {
        "title": "关于Pytest框架，以下说法正确的是？",
        "description": "关于Pytest框架，以下说法正确的是？\n\nA. Pytest是一个功能强大的Python测试框架\nB. Pytest只支持单元测试\nC. Pytest不支持插件\nD. Pytest是内置库",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "Pytest框架基础"
    },
    {
        "title": "关于Pytest的测试用例发现规则，以下说法正确的是？（多选）",
        "description": "关于Pytest的测试用例发现规则，以下说法正确的是？（多选）\n\nA. 测试文件以test_开头或_test结尾\nB. 测试函数以test_开头\nC. 测试类以Test开头\nD. Pytest无法自动发现测试用例",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Pytest框架基础"
    },
    {
        "title": "请判断：Pytest支持参数化测试（@pytest.mark.parametrize）。",
        "description": "请判断：Pytest支持参数化测试（@pytest.mark.parametrize）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Pytest框架基础"
    },
    {
        "title": "关于Pytest的Fixture，以下说法正确的是？",
        "description": "关于Pytest的Fixture，以下说法正确的是？\n\nA. Fixture用于提供测试前置和后置操作\nB. Fixture没有用\nC. Fixture只能用于单个测试函数\nD. Fixture不支持参数化",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础"
    },
    {
        "title": "关于Pytest的断言，以下说法正确的是？（多选）",
        "description": "关于Pytest的断言，以下说法正确的是？（多选）\n\nA. 可以使用assert语句\nB. 断言失败会显示详细信息\nC. 可以使用pytest.raises()断言异常\nD. Pytest不支持断言",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Pytest框架基础"
    },
    {
        "title": "请判断：Pytest可以生成HTML测试报告（使用pytest-html插件）。",
        "description": "请判断：Pytest可以生成HTML测试报告（使用pytest-html插件）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "Pytest框架基础"
    },
    {
        "title": "关于Pytest的标记（Marker），以下说法正确的是？",
        "description": "关于Pytest的标记（Marker），以下说法正确的是？\n\nA. 可以使用@pytest.mark标记测试用例\nB. 标记没有用\nC. 标记只能在命令行使用\nD. Pytest不支持标记",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础"
    },
    {
        "title": "关于Pytest的配置文件，以下说法正确的是？（多选）",
        "description": "关于Pytest的配置文件，以下说法正确的是？（多选）\n\nA. 可以使用pytest.ini或pyproject.toml\nB. 可以配置测试路径、标记、插件等\nC. 配置文件是必需的\nD. 配置文件不支持自定义标记",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础"
    },
    {
        "title": "请判断：Pytest支持并行执行测试（使用pytest-xdist插件）。",
        "description": "请判断：Pytest支持并行执行测试（使用pytest-xdist插件）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "Pytest框架基础"
    },
    {
        "title": "关于Pytest的用例执行顺序，以下说法正确的是？",
        "description": "关于Pytest的用例执行顺序，以下说法正确的是？\n\nA. 默认按文件内容和函数名排序执行\nB. Pytest会随机执行\nC. Pytest按照编写顺序执行\nD. Pytest不支持控制执行顺序",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Pytest框架基础"
    },
    
    # ============ 接口自动化测试实战（15题）============
    {
        "title": "关于接口自动化测试的框架搭建，以下说法正确的是？",
        "description": "关于接口自动化测试的框架搭建，以下说法正确的是？\n\nA. 应该分层设计：测试用例层、业务逻辑层、工具层\nB. 所有代码写在一个文件里\nC. 不需要框架，直接写脚本即可\nD. 框架越复杂越好",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试用例的组织，以下说法正确的是？（多选）",
        "description": "关于接口测试用例的组织，以下说法正确的是？（多选）\n\nA. 应该按模块或业务场景组织\nB. 应该使用配置文件管理接口地址、测试数据\nC. 应该提取公共操作到基类或工具类\nD. 所有用例写在一个文件里",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "请判断：接口自动化测试应该验证状态码、响应体、响应时间等。",
        "description": "请判断：接口自动化测试应该验证状态码、响应体、响应时间等。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口依赖处理，以下说法正确的是？",
        "description": "关于接口依赖处理，以下说法正确的是？\n\nA. 应该在一个测试用例中完成依赖调用\nB. 接口之间没有依赖\nC. 依赖处理很复杂，不需要测试\nD. 依赖只能手动处理",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于测试数据的管理，以下说法正确的是？（多选）",
        "description": "关于测试数据的管理，以下说法正确的是？（多选）\n\nA. 应该使用独立的测试数据文件（如：JSON、YAML）\nB. 可以使用Pytest的Fixture准备测试数据\nC. 应该保证测试数据的独立性和可重复性\nD. 测试数据硬编码在脚本中",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "请判断：接口自动化测试应该生成详细的测试报告。",
        "description": "请判断：接口自动化测试应该生成详细的测试报告。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试的断言设计，以下说法正确的是？",
        "description": "关于接口测试的断言设计，以下说法正确的是？\n\nA. 应该断言状态码、关键字段、数据类型等\nB. 只需要断言状态码\nC. 断言越多越好\nD. 不需要断言",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试的日志，以下说法正确的是？（多选）",
        "description": "关于接口测试的日志，以下说法正确的是？（多选）\n\nA. 应该记录请求和响应的详细信息\nB. 日志应该便于调试和问题定位\nC. 可以使用Python的logging模块\nD. 日志不重要，可以不需要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "请判断：接口自动化测试应该与CI/CD流水线集成。",
        "description": "请判断：接口自动化测试应该与CI/CD流水线集成。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试的异常处理，以下说法正确的是？",
        "description": "关于接口测试的异常处理，以下说法正确的是？\n\nA. 应该捕获并记录异常，生成失败的测试报告\nB. 异常不需要处理\nC. 异常直接导致测试中断\nD. 异常处理很复杂，不需要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试的执行策略，以下说法正确的是？（多选）",
        "description": "关于接口测试的执行策略，以下说法正确的是？（多选）\n\nA. 应该支持按模块、按场景、按优先级执行\nB. 应该支持失败重试\nC. 应该快速反馈测试结果\nD. 所有测试必须一次执行完",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "请判断：接口自动化测试应该定期执行（如：每天定时执行）。",
        "description": "请判断：接口自动化测试应该定期执行（如：每天定时执行）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试的报告内容，以下说法正确的是？",
        "description": "关于接口测试的报告内容，以下说法正确的是？\n\nA. 应该包括：用例执行结果、请求响应详情、错误信息、通过率\nB. 报告只需要显示通过率\nC. 报告越简单越好\nD. 报告不需要详细信息",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "关于接口测试的维护，以下说法正确的是？（多选）",
        "description": "关于接口测试的维护，以下说法正确的是？（多选）\n\nA. 接口变更时应该及时更新测试脚本\nB. 应该定期回顾和优化测试用例\nC. 应该使用Page Object或类似模式提高可维护性\nD. 测试脚本写好就不需要维护",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "接口自动化测试实战"
    },
    {
        "title": "请判断：接口自动化测试可以提高测试效率，但不能完全替代手工测试。",
        "description": "请判断：接口自动化测试可以提高测试效率，但不能完全替代手工测试。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "接口自动化测试实战"
    },
    
    # ============ 高级话题（15题）============
    {
        "title": "关于接口mock，以下说法正确的是？",
        "description": "关于接口mock，以下说法正确的是？\n\nA. Mock可以模拟未完成的接口或外部依赖\nB. Mock没有用\nC. Mock只能用于单元测试\nD. Mock很复杂，不需要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "高级话题"
    },
    {
        "title": "请判断：可以使用requests-mock库模拟HTTP请求。",
        "description": "请判断：可以使用requests-mock库模拟HTTP请求。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题"
    },
    {
        "title": "关于接口性能测试，以下说法正确的是？（多选）",
        "description": "关于接口性能测试，以下说法正确的是？（多选）\n\nA. 可以使用Locust、JMeter等工具\nB. 应该测试接口的响应时间、吞吐量、并发用户数\nC. 接口性能测试很重要\nD. 接口性能测试不需要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题"
    },
    {
        "title": "请判断：接口自动化测试应该包含安全测试（如：SQL注入、XSS等）。",
        "description": "请判断：接口自动化测试应该包含安全测试（如：SQL注入、XSS等）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "高级话题"
    },
    {
        "title": "关于接口测试的最佳实践，以下说法正确的是？",
        "description": "关于接口测试的最佳实践，以下说法正确的是？\n\nA. 应该遵循：独立性、可重复性、快速反馈、易于维护\nB. 最佳实践不重要\nC. 最佳实践很复杂\nD. 不需要最佳实践",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "高级话题"
    },
    {
        "title": "关于接口自动化测试的未来趋势，以下说法正确的是？（多选）",
        "description": "关于接口自动化测试的未来趋势，以下说法正确的是？（多选）\n\nA. AI辅助生成测试用例\nB. 更多的云原生和容器化支持\nC. 更智能的测试报告和缺陷定位\nD. 接口测试会被淘汰",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "高级话题"
    },
]

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 删除学习路径11的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 11")
    print("🗑️  已删除学习路径11（接口自动化测试 - Requests+Pytest）的旧习题")
    
    # 插入50道精品题
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex['exercise_type'] == 'code' else "中文"
            
            cursor.execute("""
                INSERT INTO exercises 
                (title, description, solution, exercise_type, difficulty, 
                 learning_path_id, category, is_public, language, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 11, ?, 1, ?, datetime('now'), datetime('now'))
            """, (
                ex['title'],
                ex['description'],
                ex['solution'],
                ex['exercise_type'],
                ex['difficulty'],
                ex['category'],
                lang
            ))
            inserted += 1
        except Exception as e:
            print(f"⚠️  插入失败: {e}")
            continue
    
    conn.commit()
    
    # 更新 learning_paths 的 exercise_count
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 11", (inserted,))
    conn.commit()
    
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径11（接口自动化测试 - Requests+Pytest）")
    
    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 11")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径11现在有 {count} 道习题")
    
    conn.close()

if __name__ == "__main__":
    main()
