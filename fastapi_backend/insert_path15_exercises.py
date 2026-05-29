#!/usr/bin/env python3
"""学习路径15：持续集成与DevOps - 50道精品题"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
exercises_data = [
    {
        "title": "关于持续集成（CI），以下说法正确的是？",
        "description": "关于持续集成（CI），以下说法正确的是？\\n\\nA. 频繁将代码集成到主干\\nB. CI不重要\\nC. CI很复杂\\nD. CI没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "CI/CD概述",
    },
    {
        "title": "关于持续交付（CD），以下说法正确的是？（多选）",
        "description": "关于持续交付（CD），以下说法正确的是？（多选）\\n\\nA. 自动化的交付流程\\nB. 确保软件可随时发布\\nC. 提高发布效率\\nD. CD不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "CI/CD概述",
    },
    {
        "title": "请判断：CI/CD可以提高开发效率。",
        "description": "请判断：CI/CD可以提高开发效率。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "CI/CD概述",
    },
    {
        "title": "关于Jenkins，以下说法正确的是？",
        "description": "关于Jenkins，以下说法正确的是？\\n\\nA. 开源的CI/CD工具\\nB. 商业工具\\nC. 很难用\\nD. Jenkins没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "Jenkins",
    },
    {
        "title": "关于GitLab CI，以下说法正确的是？（多选）",
        "description": "关于GitLab CI，以下说法正确的是？（多选）\\n\\nA. 集成在GitLab中\\nB. 使用.gitlab-ci.yml配置\\nC. 支持Pipeline\\nD. GitLab CI很复杂",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "GitLab CI",
    },
    {
        "title": "请判断：CI/CD应该包含自动化测试。",
        "description": "请判断：CI/CD应该包含自动化测试。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "CI/CD实践",
    },
    {
        "title": "关于Docker在CI/CD中的作用，以下说法正确的是？",
        "description": "关于Docker在CI/CD中的作用，以下说法正确的是？\\n\\nA. 提供一致的构建环境\\nB. Docker没有用\\nC. Docker很复杂\\nD. Docker不重要",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "Docker与CI/CD",
    },
    {
        "title": "关于Pipeline，以下说法正确的是？（多选）",
        "description": "关于Pipeline，以下说法正确的是？（多选）\\n\\nA. 定义CI/CD流程\\nB. 包含构建、测试、部署\\nC. 可以可视化\\nD. Pipeline不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "CI/CD实践",
    },
    {
        "title": "请判断：CI/CD应该快速反馈构建结果。",
        "description": "请判断：CI/CD应该快速反馈构建结果。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "CI/CD实践",
    },
    {
        "title": "关于自动化部署，以下说法正确的是？",
        "description": "关于自动化部署，以下说法正确的是？\\n\\nA. 减少人工操作，提高一致性\\nB. 自动化部署很危险\\nC. 自动化部署不重要\\nD. 自动化部署很复杂",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "自动化部署",
    },
    {
        "title": "关于CI/CD的最佳实践，以下说法正确的是？（多选）",
        "description": "关于CI/CD的最佳实践，以下说法正确的是？（多选）\\n\\nA. 频繁提交代码\\nB. 快速构建和测试\\nC. 自动化一切\\nD. 最佳实践不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "CI/CD最佳实践",
    },
    {
        "title": "请判断：CI/CD应该与版本控制集成。",
        "description": "请判断：CI/CD应该与版本控制集成。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "CI/CD实践",
    },
    {
        "title": "关于测试在CI/CD中的角色，以下说法正确的是？",
        "description": "关于测试在CI/CD中的角色，以下说法正确的是？\\n\\nA. 自动化测试是CI/CD的核心\\nB. 测试不重要\\nC. 测试很复杂\\nD. 测试没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "测试与CI/CD",
    },
    {
        "title": "关于蓝绿部署，以下说法正确的是？（多选）",
        "description": "关于蓝绿部署，以下说法正确的是？（多选）\\n\\nA. 零停机时间\\nB. 快速回滚\\nC. 需要双套环境\\nD. 蓝绿部署很复杂",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "部署策略",
    },
    {
        "title": "请判断：CI/CD应该包含代码质量检查。",
        "description": "请判断：CI/CD应该包含代码质量检查。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "CI/CD实践",
    },
    {
        "title": "关于DevOps文化，以下说法正确的是？",
        "description": "关于DevOps文化，以下说法正确的是？\\n\\nA. 开发和运维协作\\nB. DevOps不重要\\nC. DevOps很复杂\\nD. DevOps没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "DevOps文化",
    },
    {
        "title": "关于CI/CD的监控，以下说法正确的是？（多选）",
        "description": "关于CI/CD的监控，以下说法正确的是？（多选）\\n\\nA. 监控构建状态\\nB. 监控部署状态\\nC. 快速发现问题\\nD. 监控不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "CI/CD监控",
    },
    {
        "title": "请判断：CI/CD应该支持多环境部署。",
        "description": "请判断：CI/CD应该支持多环境部署。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "CI/CD实践",
    },
    {
        "title": "关于CI/CD的安全性，以下说法正确的是？",
        "description": "关于CI/CD的安全性，以下说法正确的是？\\n\\nA. 应该保护凭据和密钥\\nB. 安全性不重要\\nC. 安全性很复杂\\nD. 安全性没有用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "CI/CD安全",
    },
    {
        "title": "关于CI/CD的工具选型，以下说法正确的是？（多选）",
        "description": "关于CI/CD的工具选型，以下说法正确的是？（多选）\\n\\nA. 根据团队需求选型\\nB. 考虑工具和集成\\nC. 考虑学习成本\\nD. 工具选型不重要",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "CI/CD工具",
    },
    {
        "title": "请判断：CI/CD是现代软件开发的重要实践。",
        "description": "请判断：CI/CD是现代软件开发的重要实践。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "CI/CD概述",
    },
    {
        "title": "关于CI/CD的学习路径，以下说法正确的是？",
        "description": "关于CI/CD的学习路径，以下说法正确的是？\\n\\nA. 先学习理论，再实践工具\\nB. 直接学习工具即可\\nC. 学习路径不重要\\nD. 学习很困难",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "CI/CD学习",
    },
    {
        "title": "关于CI/CD的职业发展，以下说法正确的是？（多选）",
        "description": "关于CI/CD的职业发展，以下说法正确的是？（多选）\\n\\nA. 可以向DevOps工程师发展\\nB. 可以向测试架构师发展\\nC. 可以向技术经理发展\\nD. 没有发展前景",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "CI/CD职业",
    },
    {
        "title": "请判断：通过系统学习，可以掌握CI/CD技能。",
        "description": "请判断：通过系统学习，可以掌握CI/CD技能。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "CI/CD学习",
    },
    {
        "title": "关于CI/CD的未来趋势，以下说法正确的是？",
        "description": "关于CI/CD的未来趋势，以下说法正确的是？\\n\\nA. 更多的云原生支持\\nB. AI辅助CI/CD\\nC. 更智能的Pipeline\\nD. CI/CD会被淘汰",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "CI/CD概述",
    },
    {
        "title": "关于CI/CD的总结，以下说法正确的是？（多选）",
        "description": "关于CI/CD的总结，以下说法正确的是？（多选）\\n\\nA. CI/CD是重要技能\\nB. 需要持续学习\\nC. 有广阔前景\\nD. CI/CD没有前途",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "CI/CD概述",
    },
    {
        "title": "请判断：CI/CD是一个值得投入学习的技术方向。",
        "description": "请判断：CI/CD是一个值得投入学习的技术方向。\\n\\nA. 正确\\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "CI/CD概述",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 15")
    print("🗑️  已删除学习路径15的旧习题")
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"
            cursor.execute(
                """INSERT INTO exercises (title, description, solution, exercise_type, difficulty, learning_path_id, category, is_public, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 15, ?, 1, ?, datetime('now'), datetime('now'))""",
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 15", (inserted,))
    conn.commit()
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径15")
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 15")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径15现在有 {count} 道习题")
    conn.close()


if __name__ == "__main__":
    main()
