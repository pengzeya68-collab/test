#!/usr/bin/env python3
"""学习路径14：安全测试基础 - 50道精品题"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
exercises_data = [
    {
        "title": "关于安全测试，以下说法正确的是？",
        "description": "关于安全测试，以下说法正确的是？\\n\\nA. 发现系统安全漏洞\\nB. 只测试功能\\nC. 安全测试不重要\\nD. 安全测试很简单",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "安全测试概述",
    },
    {
        "title": "关于常见安全漏洞，以下说法正确的是？（多选）",
        "description": "关于常见安全漏洞，以下说法正确的是？（多选）\\n\\nA. SQL注入\\nB. XSS跨站脚本\\nC. CSRF跨站请求伪造\\nD. 没有漏洞",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "请判断：安全测试应该尽早进行。",
        "description": "请判断：安全测试应该尽早进行。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于SQL注入，以下说法正确的是？",
        "description": "关于SQL注入，以下说法正确的是？\\n\\nA. 通过在输入中插入SQL语句\\nB. SQL注入不存在\\nC. SQL注入很难防\\nD. SQL注入不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "SQL注入",
    },
    {
        "title": "关于XSS攻击，以下说法正确的是？（多选）",
        "description": "关于XSS攻击，以下说法正确的是？（多选）\\n\\nA. 反射型XSS\\nB. 存储型XSS\\nC. DOM型XSS\\nD. XSS不存在",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "XSS攻击",
    },
    {
        "title": "请判断：CSRF攻击需要用户登录状态。",
        "description": "请判断：CSRF攻击需要用户登录状态。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "CSRF攻击",
    },
    {
        "title": "关于安全测试工具，以下说法正确的是？",
        "description": "关于安全测试工具，以下说法正确的是？\\n\\nA. 包括Burp Suite、OWASP ZAP\\nB. 工具很少\\nC. 工具很昂贵\\nD. 工具没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "安全测试工具",
    },
    {
        "title": "关于渗透测试，以下说法正确的是？（多选）",
        "description": "关于渗透测试，以下说法正确的是？（多选）\\n\\nA. 模拟黑客攻击\\nB. 发现安全漏洞\\nC. 评估安全防御\\nD. 渗透测试没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "渗透测试",
    },
    {
        "title": "请判断：安全测试需要专业知识和技能。",
        "description": "请判断：安全测试需要专业知识和技能。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的报告，以下说法正确的是？",
        "description": "关于安全测试的报告，以下说法正确的是？\\n\\nA. 应该包含漏洞描述、风险等级、修复建议\\nB. 报告很简单\\nC. 报告不重要\\nD. 报告很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "安全测试报告",
    },
    {
        "title": "关于OWASP Top 10，以下说法正确的是？（多选）",
        "description": "关于OWASP Top 10，以下说法正确的是？（多选）\\n\\nA. 列出最常见的安全风险\\nB. 定期更新\\nC. 是安全测试的重要参考\\nD. OWASP Top 10没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "安全测试标准",
    },
    {
        "title": "请判断：安全测试应该定期执行。",
        "description": "请判断：安全测试应该定期执行。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于身份认证测试，以下说法正确的是？",
        "description": "关于身份认证测试，以下说法正确的是？\\n\\nA. 测试密码策略、会话管理\\nB. 认证测试很简单\\nC. 认证测试不重要\\nD. 认证测试很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "身份认证测试",
    },
    {
        "title": "关于授权测试，以下说法正确的是？（多选）",
        "description": "关于授权测试，以下说法正确的是？（多选）\\n\\nA. 测试权限控制\\nB. 测试越权访问\\nC. 测试角色权限\\nD. 授权测试没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "授权测试",
    },
    {
        "title": "请判断：安全测试应该包含配置审查。",
        "description": "请判断：安全测试应该包含配置审查。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "安全测试高级",
    },
    {
        "title": "关于加密测试，以下说法正确的是？",
        "description": "关于加密测试，以下说法正确的是？\\n\\nA. 测试数据加密传输和存储\\nB. 加密测试很简单\\nC. 加密测试不重要\\nD. 加密测试很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "加密测试",
    },
    {
        "title": "关于安全测试的最佳实践，以下说法正确的是？（多选）",
        "description": "关于安全测试的最佳实践，以下说法正确的是？（多选）\\n\\nA. 制定安全测试策略\\nB. 使用专业工具\\nC. 持续学习和实践\\nD. 最佳实践不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "安全测试最佳实践",
    },
    {
        "title": "请判断：安全测试是持续的过程。",
        "description": "请判断：安全测试是持续的过程。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的职业发展，以下说法正确的是？",
        "description": "关于安全测试的职业发展，以下说法正确的是？\\n\\nA. 可以向安全专家发展\\nB. 没有发展前景\\nC. 发展很困难\\nD. 发展不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "安全测试职业",
    },
    {
        "title": "关于安全测试的学习路径，以下说法正确的是？（多选）",
        "description": "关于安全测试的学习路径，以下说法正确的是？（多选）\\n\\nA. 学习网络基础\\nB. 学习安全工具\\nC. 学习漏洞原理\\nD. 学习路径不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "安全测试学习",
    },
    {
        "title": "请判断：安全测试是一个有前景的领域。",
        "description": "请判断：安全测试是一个有前景的领域。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的挑战，以下说法正确的是？",
        "description": "关于安全测试的挑战，以下说法正确的是？\\n\\nA. 需要持续学习\\nB. 没有挑战\\nC. 挑战无法克服\\nD. 挑战不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的工具选型，以下说法正确的是？（多选）",
        "description": "关于安全测试的工具选型，以下说法正确的是？（多选）\\n\\nA. 根据需求选择工具\\nB. 考虑工具功能\\nC. 考虑学习成本\\nD. 工具选型不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "安全测试工具",
    },
    {
        "title": "请判断：安全测试应该与开发团队协作。",
        "description": "请判断：安全测试应该与开发团队协作。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试协作",
    },
    {
        "title": "关于安全测试的报告编写，以下说法正确的是？",
        "description": "关于安全测试的报告编写，以下说法正确的是？\\n\\nA. 应该清晰描述漏洞和风险\\nB. 报告很简单\\nC. 报告不重要\\nD. 报告很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "安全测试报告",
    },
    {
        "title": "关于安全测试的持续学习，以下说法正确的是？（多选）",
        "description": "关于安全测试的持续学习，以下说法正确的是？（多选）\\n\\nA. 关注安全动态\\nB. 学习新漏洞\\nC. 实践渗透技术\\nD. 学习不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "安全测试学习",
    },
    {
        "title": "请判断：安全测试需要遵守法律和道德。",
        "description": "请判断：安全测试需要遵守法律和道德。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试职业道德",
    },
    {
        "title": "关于安全测试的未来趋势，以下说法正确的是？",
        "description": "关于安全测试的未来趋势，以下说法正确的是？\\n\\nA. AI辅助安全测试\\nB. 未来很简单\\nC. 未来很悲观\\nD. 未来不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的社区，以下说法正确的是？（多选）",
        "description": "关于安全测试的社区，以下说法正确的是？（多选）\\n\\nA. 可以加入安全社区\\nB. 可以参加安全会议\\nC. 可以关注安全博客\\nD. 社区没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "安全测试学习",
    },
    {
        "title": "请判断：通过系统学习，可以掌握安全测试技能。",
        "description": "请判断：通过系统学习，可以掌握安全测试技能。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
    {
        "title": "关于安全测试的价值，以下说法正确的是？",
        "description": "关于安全测试的价值，以下说法正确的是？\\n\\nA. 保护用户数据安全\\nB. 价值很难衡量\\nC. 价值不重要\\nD. 价值很有限",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的创新，以下说法正确的是？（多选）",
        "description": "关于安全测试的创新，以下说法正确的是？（多选）\\n\\nA. AI辅助漏洞发现\\nB. 自动化渗透测试\\nC. 智能化安全分析\\nD. 不需要创新",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "安全测试创新",
    },
    {
        "title": "请判断：安全测试需要关注业务逻辑漏洞。",
        "description": "请判断：安全测试需要关注业务逻辑漏洞。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "安全测试高级",
    },
    {
        "title": "关于安全测试的总结，以下说法正确的是？",
        "description": "关于安全测试的总结，以下说法正确的是？\\n\\nA. 安全测试是重要的质量保障\\nB. 总结不重要\\nC. 总结很复杂\\nD. 总结没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的资源推荐，以下说法正确的是？（多选）",
        "description": "关于安全测试的资源推荐，以下说法正确的是？（多选）\\n\\nA. OWASP官网\\nB. 安全博客\\nC. 安全书籍\\nD. 资源没有用",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "安全测试学习",
    },
    {
        "title": "请判断：安全测试是一个不断发展的领域。",
        "description": "请判断：安全测试是一个不断发展的领域。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的终极目标，以下说法正确的是？",
        "description": "关于安全测试的终极目标，以下说法正确的是？\\n\\nA. 保护系统和数据安全\\nB. 目标很难达成\\nC. 目标不重要\\nD. 目标很模糊",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的鼓励话语，以下说法正确的是？（多选）",
        "description": "关于安全测试的鼓励话语，以下说法正确的是？（多选）\\n\\nA. 安全测试有挑战性\\nB. 安全测试有发展前景\\nC. 安全测试值得投入\\nD. 鼓励和话语不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
    {
        "title": "请判断：通过努力学习和实践，一定能掌握安全测试。",
        "description": "请判断：通过努力学习和实践，一定能掌握安全测试。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
    {
        "title": "关于安全测试的祝福，以下说法正确的是？",
        "description": "关于安全测试的祝福，以下说法正确的是？\\n\\nA. 祝愿学习顺利\\nB. 祝福不重要\\nC. 祝福很虚伪\\nD. 祝福没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
    {
        "title": "关于安全测试的持续进步，以下说法正确的是？（多选）",
        "description": "关于安全测试的持续进步，以下说法正确的是？（多选）\\n\\nA. 每天进步一点点\\nB. 持续积累经验\\nC. 不断挑战自己\\nD. 进步不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
    {
        "title": "请判断：安全测试之路虽然挑战，但充满机遇。",
        "description": "请判断：安全测试之路虽然挑战，但充满机遇。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "安全测试概述",
    },
    {
        "title": "关于安全测试的最终鼓励，以下说法正确的是？",
        "description": "关于安全测试的最终鼓励，以下说法正确的是？\\n\\nA. 相信自己，坚持学习\\nB. 鼓励没有用\\nC. 鼓励很虚伪\\nD. 鼓励不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
    {
        "title": "关于安全测试的总结寄语，以下说法正确的是？（多选）",
        "description": "关于安全测试的总结寄语，以下说法正确的是？（多选）\\n\\nA. 安全测试是重要技能\\nB. 需要持续学习\\nC. 有广阔前景\\nD. 寄语不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "安全测试概述",
    },
    {
        "title": "请判断：通过本课程的学习，可以掌握安全测试基础。",
        "description": "请判断：通过本课程的学习，可以掌握安全测试基础。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "安全测试学习",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 14")
    print("🗑️  已删除学习路径14的旧习题")
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"
            cursor.execute(
                """INSERT INTO exercises (title, description, solution, exercise_type, difficulty, learning_path_id, category, is_public, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 14, ?, 1, ?, datetime('now'), datetime('now'))""",
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 14", (inserted,))
    conn.commit()
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径14")
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 14")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径14现在有 {count} 道习题")
    conn.close()


if __name__ == "__main__":
    main()
