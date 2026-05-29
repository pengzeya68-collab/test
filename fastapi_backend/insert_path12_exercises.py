#!/usr/bin/env python3
"""学习路径12：移动端测试基础 - 50道精品题"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
exercises_data = [
    {
        "title": "关于移动端测试，以下说法正确的是？",
        "description": "关于移动端测试，以下说法正确的是？\n\nA. 包括功能测试、兼容性测试、性能测试\nB. 移动端测试只测试功能\nC. 移动端测试很简单\nD. 移动端测试不需要工具",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的挑战，以下说法正确的是？（多选）",
        "description": "关于移动端测试的挑战，以下说法正确的是？（多选）\n\nA. 设备碎片化\nB. 操作系统版本多\nC. 网络环境复杂\nD. 移动端测试没有挑战",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "移动端测试概述",
    },
    {
        "title": "请判断：移动端测试需要覆盖不同的设备和系统版本。",
        "description": "请判断：移动端测试需要覆盖不同的设备和系统版本。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "移动端测试概述",
    },
    {
        "title": "关于Android测试，以下说法正确的是？",
        "description": "关于Android测试，以下说法正确的是？\n\nA. 可以使用Android Studio、ADB工具\nB. Android测试只能手工进行\nC. Android测试不需要工具\nD. Android测试很简单",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Android测试",
    },
    {
        "title": "关于iOS测试，以下说法正确的是？（多选）",
        "description": "关于iOS测试，以下说法正确的是？（多选）\n\nA. 可以使用Xcode、Instruments\nB. iOS测试需要Mac环境\nC. iOS测试可以使用真机或模拟器\nD. iOS测试很简单",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "iOS测试",
    },
    {
        "title": "请判断：移动端性能测试包括CPU、内存、电量、流量等。",
        "description": "请判断：移动端性能测试包括CPU、内存、电量、流量等。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端性能测试",
    },
    {
        "title": "关于移动端自动化测试工具，以下说法正确的是？",
        "description": "关于移动端自动化测试工具，以下说法正确的是？\n\nA. 包括Appium、Airtest、UI Automator\nB. 移动端自动化工具很少\nC. 移动端无法自动化\nD. 移动端自动化很昂贵",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端自动化测试",
    },
    {
        "title": "关于Appium，以下说法正确的是？（多选）",
        "description": "关于Appium，以下说法正确的是？（多选）\n\nA. 支持Android和iOS\nB. 支持多种编程语言\nC. 基于WebDriver协议\nD. Appium只支持Android",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端自动化测试",
    },
    {
        "title": "请判断：移动端测试需要测试弱网环境。",
        "description": "请判断：移动端测试需要测试弱网环境。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端网络测试",
    },
    {
        "title": "关于移动端兼容性测试，以下说法正确的是？",
        "description": "关于移动端兼容性测试，以下说法正确的是？\n\nA. 应该覆盖主流设备和系统版本\nB. 兼容性测试不重要\nC. 只需要测试最新设备\nD. 兼容性测试很昂贵",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端兼容性测试",
    },
    {
        "title": "关于移动端安全测试，以下说法正确的是？（多选）",
        "description": "关于移动端安全测试，以下说法正确的是？（多选）\n\nA. 应该测试数据加密、权限管理\nB. 应该测试反编译和篡改\nC. 应该测试网络传输安全\nD. 安全测试不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端安全测试",
    },
    {
        "title": "请判断：移动端测试需要测试安装、卸载、升级等场景。",
        "description": "请判断：移动端测试需要测试安装、卸载、升级等场景。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端功能测试",
    },
    {
        "title": "关于移动端测试的环境，以下说法正确的是？",
        "description": "关于移动端测试的环境，以下说法正确的是？\n\nA. 可以使用真机或模拟器\nB. 只能使用真机\nC. 只能使用模拟器\nD. 环境不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "移动端测试环境",
    },
    {
        "title": "关于ADB命令，以下说法正确的是？（多选）",
        "description": "关于ADB命令，以下说法正确的是？（多选）\n\nA. 可以安装/卸载应用\nB. 可以查看设备日志\nC. 可以传输文件\nD. ADB只能用于调试",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Android测试",
    },
    {
        "title": "请判断：移动端测试需要关注用户体验。",
        "description": "请判断：移动端测试需要关注用户体验。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的最佳实践，以下说法正确的是？",
        "description": "关于移动端测试的最佳实践，以下说法正确的是？\n\nA. 应该制定测试策略、选择合适的工具\nB. 最佳实践不重要\nC. 最佳实践很复杂\nD. 不需要最佳实践",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端测试最佳实践",
    },
    {
        "title": "关于移动端测试的难点，以下说法正确的是？（多选）",
        "description": "关于移动端测试的难点，以下说法正确的是？（多选）\n\nA. 设备碎片化严重\nB. 操作系统版本多\nC. 网络环境复杂\nD. 移动端测试没有难点",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试概述",
    },
    {
        "title": "请判断：移动端测试应该自动化。",
        "description": "请判断：移动端测试应该自动化。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端自动化测试",
    },
    {
        "title": "关于移动端测试的报告，以下说法正确的是？",
        "description": "关于移动端测试的报告，以下说法正确的是？\n\nA. 应该包含设备信息、测试结果、日志\nB. 报告只需要通过率\nC. 报告不重要\nD. 报告很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "移动端测试报告",
    },
    {
        "title": "关于移动端测试的未来趋势，以下说法正确的是？（多选）",
        "description": "关于移动端测试的未来趋势，以下说法正确的是？（多选）\n\nA. AI辅助测试\nB. 云测试平台\nC. 更多的自动化工具\nD. 移动端测试会被淘汰",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试概述",
    },
    {
        "title": "请判断：移动端测试需要测试横竖屏切换。",
        "description": "请判断：移动端测试需要测试横竖屏切换。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端功能测试",
    },
    {
        "title": "关于移动端测试的工具选型，以下说法正确的是？",
        "description": "关于移动端测试的工具选型，以下说法正确的是？\n\nA. 应该根据项目需求、团队技能选型\nB. 商业工具一定好\nC. 开源工具不好\nD. 工具选型不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端测试工具",
    },
    {
        "title": "关于移动端测试的持续集成，以下说法正确的是？（多选）",
        "description": "关于移动端测试的持续集成，以下说法正确的是？（多选）\n\nA. 可以集成到CI/CD流水线\nB. 应该自动化执行\nC. 应该快速反馈\nD. 持续集成不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试CI/CD",
    },
    {
        "title": "请判断：移动端测试需要测试推送通知。",
        "description": "请判断：移动端测试需要测试推送通知。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端功能测试",
    },
    {
        "title": "关于移动端测试的性能指标，以下说法正确的是？",
        "description": "关于移动端测试的性能指标，以下说法正确的是？\n\nA. 包括启动时间、响应时间、电量消耗\nB. 性能指标不重要\nC. 只关注启动时间\nD. 性能指标很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端性能测试",
    },
    {
        "title": "关于移动端测试的回归测试，以下说法正确的是？（多选）",
        "description": "关于移动端测试的回归测试，以下说法正确的是？（多选）\n\nA. 应该自动化回归测试\nB. 应该覆盖核心功能\nC. 应该定期执行\nD. 回归测试不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端回归测试",
    },
    {
        "title": "请判断：移动端测试需要测试不同分辨率的设备。",
        "description": "请判断：移动端测试需要测试不同分辨率的设备。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端兼容性测试",
    },
    {
        "title": "关于移动端测试的挑战与对策，以下说法正确的是？",
        "description": "关于移动端测试的挑战与对策，以下说法正确的是？\n\nA. 应该制定测试策略、使用云测试平台\nB. 挑战无法解决\nC. 对策很复杂\nD. 不需要对策",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的知识体系，以下说法正确的是？（多选）",
        "description": "关于移动端测试的知识体系，以下说法正确的是？（多选）\n\nA. 包括测试理论、工具使用、编程技能\nB. 应该持续学习\nC. 应该实践积累\nD. 知识体系不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试概述",
    },
    {
        "title": "请判断：移动端测试是软件测试的重要分支。",
        "description": "请判断：移动端测试是软件测试的重要分支。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的学习路径，以下说法正确的是？",
        "description": "关于移动端测试的学习路径，以下说法正确的是？\n\nA. 应该先学习基础理论，再实践工具\nB. 直接学习工具即可\nC. 学习路径不重要\nD. 学习很困难",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "移动端测试学习",
    },
    {
        "title": "关于移动端测试的职业发展，以下说法正确的是？（多选）",
        "description": "关于移动端测试的职业发展，以下说法正确的是？（多选）\n\nA. 可以向测试开发方向发展\nB. 可以向测试架构师发展\nC. 可以向产品经理发展\nD. 没有发展前景",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "移动端测试职业",
    },
    {
        "title": "请判断：移动端测试需要不断学习和实践。",
        "description": "请判断：移动端测试需要不断学习和实践。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "移动端测试学习",
    },
    {
        "title": "关于移动端测试的价值，以下说法正确的是？",
        "description": "关于移动端测试的价值，以下说法正确的是？\n\nA. 提高移动应用质量，改善用户体验\nB. 测试没有价值\nC. 价值很难衡量\nD. 价值不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的创新，以下说法正确的是？（多选）",
        "description": "关于移动端测试的创新，以下说法正确的是？（多选）\n\nA. AI辅助测试\nB. 云测试平台\nC. 智能化测试工具\nD. 不需要创新",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试创新",
    },
    {
        "title": "请判断：移动端测试需要关注无障碍访问。",
        "description": "请判断：移动端测试需要关注无障碍访问。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "移动端测试高级",
    },
    {
        "title": "关于移动端测试的国际化，以下说法正确的是？",
        "description": "关于移动端测试的国际化，以下说法正确的是？\n\nA. 应该测试多语言、多时区、多货币\nB. 国际化测试不重要\nC. 只测试中文即可\nD. 国际化很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "移动端测试高级",
    },
    {
        "title": "关于移动端测试的本地化，以下说法正确的是？（多选）",
        "description": "关于移动端测试的本地化，以下说法正确的是？（多选）\n\nA. 应该测试本地化语言、文化、法律\nB. 应该测试本地化格式（日期、数字）\nC. 本地化测试很重要\nD. 本地化测试不需要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试高级",
    },
    {
        "title": "请判断：移动端测试需要测试应用间的跳转。",
        "description": "请判断：移动端测试需要测试应用间的跳转。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端功能测试",
    },
    {
        "title": "关于移动端测试的未来，以下说法正确的是？",
        "description": "关于移动端测试的未来，以下说法正确的是？\n\nA. 移动端测试会越来越重要\nB. 移动端测试会被淘汰\nC. 未来很简单\nD. 未来很悲观",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的总结，以下说法正确的是？（多选）",
        "description": "关于移动端测试的总结，以下说法正确的是？（多选）\n\nA. 移动端测试是重要技能\nB. 需要持续学习和实践\nC. 有广阔的发展前景\nD. 移动端测试没有前途",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "移动端测试概述",
    },
    {
        "title": "请判断：通过系统学习，可以掌握移动端测试技能。",
        "description": "请判断：通过系统学习，可以掌握移动端测试技能。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "移动端测试学习",
    },
    {
        "title": "关于移动端测试的推荐资源，以下说法正确的是？",
        "description": "关于移动端测试的推荐资源，以下说法正确的是？\n\nA. 包括官方文档、技术博客、开源项目\nB. 资源很少\nC. 资源没有用\nD. 不需要学习资源",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "移动端测试学习",
    },
    {
        "title": "关于移动端测试的社区，以下说法正确的是？（多选）",
        "description": "关于移动端测试的社区，以下说法正确的是？（多选）\n\nA. 可以加入测试社区、技术论坛\nB. 可以参加技术会议、线下活动\nC. 可以关注技术大牛、博客\nD. 社区没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "移动端测试学习",
    },
    {
        "title": "请判断：移动端测试是一个有挑战和有价值的领域。",
        "description": "请判断：移动端测试是一个有挑战和有价值的领域。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "移动端测试概述",
    },
    {
        "title": "关于移动端测试的进阶学习，以下说法正确的是？（多选）",
        "description": "关于移动端测试的进阶学习，以下说法正确的是？（多选）\n\nA. 可以学习性能优化\nB. 可以学习安全测试\nC. 可以学习自动化框架开发\nD. 不需要进阶学习",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试学习",
    },
    {
        "title": "请判断：移动端测试需要关注电量消耗。",
        "description": "请判断：移动端测试需要关注电量消耗。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "移动端性能测试",
    },
    {
        "title": "关于移动端测试的云平台建设，以下说法正确的是？（多选）",
        "description": "关于移动端测试的云平台建设，以下说法正确的是？（多选）\n\nA. 可以使用云测试平台覆盖更多设备\nB. 云平台可以提高测试效率\nC. 云平台可以降低设备成本\nD. 云平台没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "移动端测试高级",
    },
    {
        "title": "请判断：移动端测试应该包含兼容性矩阵管理。",
        "description": "请判断：移动端测试应该包含兼容性矩阵管理。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "移动端兼容性测试",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 12")
    print("🗑️  已删除学习路径12的旧习题")
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"
            cursor.execute(
                """INSERT INTO exercises (title, description, solution, exercise_type, difficulty, learning_path_id, category, is_public, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 12, ?, 1, ?, datetime('now'), datetime('now'))""",
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 12", (inserted,))
    conn.commit()
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径12")
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 12")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径12现在有 {count} 道习题")
    conn.close()


if __name__ == "__main__":
    main()
