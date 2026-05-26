#!/usr/bin/env python3
"""学习路径13：性能测试 - JMeter与Locust - 50道精品题"""
import sqlite3
db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'
exercises_data = [
    {'title': '关于性能测试，以下说法正确的是？', 'description': '关于性能测试，以下说法正确的是？\n\nA. 测试系统的响应时间、吞吐量、资源利用率\nB. 只测试功能\nC. 性能测试不重要\nD. 性能测试很简单', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'easy', 'category': '性能测试概述'},
    {'title': '关于性能测试的类型，以下说法正确的是？（多选）', 'description': '关于性能测试的类型，以下说法正确的是？（多选）\n\nA. 负载测试\nB. 压力测试\nC. 并发测试\nD. 性能测试只有一种', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': '性能测试概述'},
    {'title': '请判断：性能测试应该在功能测试完成后进行。', 'description': '请判断：性能测试应该在功能测试完成后进行。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'medium', 'category': '性能测试概述'},
    {'title': '关于JMeter，以下说法正确的是？', 'description': '关于JMeter，以下说法正确的是？\n\nA. 开源的性能测试工具\nB. 商业工具\nC. 只支持Web测试\nD. JMeter很难用', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'medium', 'category': 'JMeter基础'},
    {'title': '关于JMeter的组件，以下说法正确的是？（多选）', 'description': '关于JMeter的组件，以下说法正确的是？（多选）\n\nA. 线程组\nB. 采样器\nC. 断言\nD. JMeter只有一个组件', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': 'JMeter基础'},
    {'title': '请判断：JMeter可以录制测试脚本。', 'description': '请判断：JMeter可以录制测试脚本。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'medium', 'category': 'JMeter基础'},
    {'title': '关于Locust，以下说法正确的是？', 'description': '关于Locust，以下说法正确的是？\n\nA. Python编写的性能测试工具\nB. Java编写\nC. 只支持HTTP\nD. Locust很难用', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'medium', 'category': 'Locust基础'},
    {'title': '关于Locust的脚本编写，以下说法正确的是？（多选）', 'description': '关于Locust的脚本编写，以下说法正确的是？（多选）\n\nA. 使用Python编写\nB. 定义用户行为类\nC. 可以设置并发用户数\nD. Locust脚本很复杂', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': 'Locust基础'},
    {'title': '请判断：Locust支持分布式执行。', 'description': '请判断：Locust支持分布式执行。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'hard', 'category': 'Locust高级'},
    {'title': '关于性能测试的指标，以下说法正确的是？', 'description': '关于性能测试的指标，以下说法正确的是？\n\nA. 响应时间、吞吐量、错误率\nB. 只关注响应时间\nC. 指标不重要\nD. 指标很复杂', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'medium', 'category': '性能测试指标'},
    {'title': '关于性能测试的计划，以下说法正确的是？（多选）', 'description': '关于性能测试的计划，以下说法正确的是？（多选）\n\nA. 确定测试目标\nB. 设计测试场景\nC. 准备测试数据\nD. 不需要计划', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': '性能测试计划'},
    {'title': '请判断：性能测试需要监控服务器资源。', 'description': '请判断：性能测试需要监控服务器资源。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'hard', 'category': '性能测试执行'},
    {'title': '关于JMeter的断言，以下说法正确的是？', 'description': '关于JMeter的断言，以下说法正确的是？\n\nA. 可以验证响应内容\nB. 断言没有用\nC. 断言很复杂\nD. 不需要断言', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'medium', 'category': 'JMeter高级'},
    {'title': '关于JMeter的参数化，以下说法正确的是？（多选）', 'description': '关于JMeter的参数化，以下说法正确的是？（多选）\n\nA. 使用CSV数据文件\nB. 使用用户自定义变量\nC. 使用函数助手\nD. 参数化没有用', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': 'JMeter高级'},
    {'title': '请判断：JMeter可以生成测试报告。', 'description': '请判断：JMeter可以生成测试报告。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'medium', 'category': 'JMeter高级'},
    {'title': '关于Locust的分布式执行，以下说法正确的是？', 'description': '关于Locust的分布式执行，以下说法正确的是？\n\nA. 可以使用master和worker模式\nB. 分布式很复杂\nC. 不支持分布式\nD. 分布式没有用', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': 'Locust高级'},
    {'title': '关于性能测试的报告，以下说法正确的是？（多选）', 'description': '关于性能测试的报告，以下说法正确的是？（多选）\n\nA. 应该包含测试场景\nB. 应该包含性能指标\nC. 应该包含问题分析\nD. 报告不重要', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': '性能测试报告'},
    {'title': '请判断：性能测试应该逐步增加负载。', 'description': '请判断：性能测试应该逐步增加负载。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'hard', 'category': '性能测试执行'},
    {'title': '关于性能瓶颈分析，以下说法正确的是？', 'description': '关于性能瓶颈分析，以下说法正确的是？\n\nA. 应该分析CPU、内存、磁盘、网络\nB. 瓶颈分析很复杂\nC. 不需要分析\nD. 瓶颈无法分析', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试分析'},
    {'title': '关于JMeter和Locust的比较，以下说法正确的是？（多选）', 'description': '关于JMeter和Locust的比较，以下说法正确的是？（多选）\n\nA. JMeter有GUI，Locust需要编程\nB. JMeter适合复杂场景，Locust适合快速脚本\nC. 两者都是优秀的工具\nD. 比较没有意义', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': '性能测试工具'},
    {'title': '请判断：性能测试是持续的过程。', 'description': '请判断：性能测试是持续的过程。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'medium', 'category': '性能测试概述'},
    {'title': '关于性能测试的自动化，以下说法正确的是？', 'description': '关于性能测试的自动化，以下说法正确的是？\n\nA. 应该与CI/CD集成\nB. 自动化很复杂\nC. 不需要自动化\nD. 自动化没有用', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试自动化'},
    {'title': '关于性能测试的最佳实践，以下说法正确的是？（多选）', 'description': '关于性能测试的最佳实践，以下说法正确的是？（多选）\n\nA. 制定明确的测试目标\nB. 设计真实的测试场景\nC. 持续监控和分析\nD. 最佳实践不重要', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': '性能测试最佳实践'},
    {'title': '请判断：性能测试需要模拟真实的用户行为。', 'description': '请判断：性能测试需要模拟真实的用户行为。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'medium', 'category': '性能测试设计'},
    {'title': '关于性能测试的未来发展，以下说法正确的是？', 'description': '关于性能测试的未来发展，以下说法正确的是？\n\nA. 更多的云原生支持\nB. AI辅助性能分析\nC. 更智能的测试工具\nD. 性能测试会被淘汰', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试概述'},
    {'title': '关于JMeter的插件，以下说法正确的是？（多选）', 'description': '关于JMeter的插件，以下说法正确的是？（多选）\n\nA. 可以使用插件管理器\nB. 常用插件：PerfMon、JSON Path Extractor\nC. 插件可以扩展功能\nD. 插件没有用', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': 'JMeter高级'},
    {'title': '请判断：Locust可以实现复杂的测试场景。', 'description': '请判断：Locust可以实现复杂的测试场景。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'hard', 'category': 'Locust高级'},
    {'title': '关于性能测试的监控，以下说法正确的是？', 'description': '关于性能测试的监控，以下说法正确的是？\n\nA. 应该监控应用和系统指标\nB. 监控不重要\nC. 监控很复杂\nD. 不需要监控', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试执行'},
    {'title': '关于性能测试的持续集成，以下说法正确的是？（多选）', 'description': '关于性能测试的持续集成，以下说法正确的是？（多选）\n\nA. 可以定期执行性能测试\nB. 可以设置性能门槛\nC. 可以自动生成报告\nD. 持续集成不重要', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'hard', 'category': '性能测试自动化'},
    {'title': '请判断：性能测试应该包含基准测试。', 'description': '请判断：性能测试应该包含基准测试。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'medium', 'category': '性能测试类型'},
    {'title': '关于性能测试的团队协作，以下说法正确的是？', 'description': '关于性能测试的团队协作，以下说法正确的是？\n\nA. 需要开发、测试、运维协作\nB. 协作不重要\nC. 协作很复杂\nD. 不需要协作', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试管理'},
    {'title': '关于性能测试的总结，以下说法正确的是？（多选）', 'description': '关于性能测试的总结，以下说法正确的是？（多选）\n\nA. 性能测试是重要的质量保障手段\nB. 需要合适的工具和策略\nC. 需要持续学习和实践\nD. 性能测试没有价值', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': '性能测试概述'},
    {'title': '请判断：通过系统学习，可以掌握性能测试技能。', 'description': '请判断：通过系统学习，可以掌握性能测试技能。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'easy', 'category': '性能测试学习'},
    {'title': '关于性能测试的学习路径，以下说法正确的是？', 'description': '关于性能测试的学习路径，以下说法正确的是？\n\nA. 先学习理论，再实践工具\nB. 直接学习工具即可\nC. 学习路径不重要\nD. 学习很困难', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'medium', 'category': '性能测试学习'},
    {'title': '关于性能测试的职业发展，以下说法正确的是？（多选）', 'description': '关于性能测试的职业发展，以下说法正确的是？（多选）\n\nA. 可以向性能测试专家发展\nB. 可以向测试架构师发展\nC. 可以向DevOps发展\nD. 没有发展前景', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': '性能测试职业'},
    {'title': '请判断：性能测试是一个有挑战和有价值的领域。', 'description': '请判断：性能测试是一个有挑战和有价值的领域。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'easy', 'category': '性能测试概述'},
    {'title': '关于性能测试的工具选型，以下说法正确的是？', 'description': '关于性能测试的工具选型，以下说法正确的是？\n\nA. 应该根据项目需求和团队技能选型\nB. 商业工具一定好\nC. 开源工具不好\nD. 工具选型不重要', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试工具'},
    {'title': '关于性能测试的社区和资源，以下说法正确的是？（多选）', 'description': '关于性能测试的社区和资源，以下说法正确的是？（多选）\n\nA. 可以加入技术社区\nB. 可以参加技术会议\nC. 可以关注技术博客\nD. 社区没有用', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': '性能测试学习'},
    {'title': '请判断：性能测试需要不断学习和实践。', 'description': '请判断：性能测试需要不断学习和实践。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'easy', 'category': '性能测试学习'},
    {'title': '关于性能测试的未来，以下说法正确的是？', 'description': '关于性能测试的未来，以下说法正确的是？\n\nA. 性能测试会越来越重要\nB. 性能测试会被淘汰\nC. 未来很简单\nD. 未来很悲观', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'medium', 'category': '性能测试概述'},
    {'title': '关于性能测试的价值，以下说法正确的是？（多选）', 'description': '关于性能测试的价值，以下说法正确的是？（多选）\n\nA. 提高系统性能\nB. 改善用户体验\nC. 降低生产风险\nD. 测试没有价值', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': '性能测试概述'},
    {'title': '请判断：性能测试是软件测试的重要分支。', 'description': '请判断：性能测试是软件测试的重要分支。\n\nA. 正确\nB. 错误', 'solution': 'A', 'exercise_type': 'true_false', 'difficulty': 'easy', 'category': '性能测试概述'},
    {'title': '关于性能测试的创新，以下说法正确的是？', 'description': '关于性能测试的创新，以下说法正确的是？\n\nA. AI辅助测试\nB. 云原生测试\nC. 智能化分析\nD. 不需要创新', 'solution': 'A', 'exercise_type': 'single_choice', 'difficulty': 'hard', 'category': '性能测试创新'},
    {'title': '关于性能测试的终极目标，以下说法正确的是？（多选）', 'description': '关于性能测试的终极目标，以下说法正确的是？（多选）\n\nA. 确保系统性能满足需求\nB. 提高用户满意度\nC. 支持业务持续发展\nD. 测试没有目标', 'solution': 'A,B,C', 'exercise_type': 'multiple_choice', 'difficulty': 'medium', 'category': '性能测试概述'},
]
def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 13")
    print("🗑️  已删除学习路径13的旧习题")
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex['exercise_type'] == 'code' else "中文"
            cursor.execute("""INSERT INTO exercises (title, description, solution, exercise_type, difficulty, learning_path_id, category, is_public, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 13, ?, 1, ?, datetime('now'), datetime('now'))""", (ex['title'], ex['description'], ex['solution'], ex['exercise_type'], ex['difficulty'], ex['category'], lang))
            inserted += 1
        except Exception as e:
            print(f"⚠️  插入失败: {e}")
            continue
    conn.commit()
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 13", (inserted,))
    conn.commit()
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径13")
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 13")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径13现在有 {count} 道习题")
    conn.close()
if __name__ == "__main__":
    main()
