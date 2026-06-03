"""
AI 积分系统迁移脚本

创建 3 张新表并写入 12 条默认 AI 功能积分配置。
幂等脚本，可重复运行。
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "testmaster.db"

SEED_CONFIGS = [
    ("ai_chat", "AI 导师对话", 2, "AI 导师聊天问答"),
    ("ai_code_review", "AI 代码评审", 5, "AI 审查用户提交的代码"),
    ("ai_learning_advice", "AI 学习建议", 3, "AI 个性化学习路径建议"),
    ("ai_explain_exercise", "AI 解题讲解", 3, "AI 解释习题正确答案"),
    ("interview_code_eval", "面试代码评测", 5, "面试代码自动评测"),
    ("interview_text_eval", "面试文本评测", 3, "面试文字题 AI 评测"),
    ("interview_follow_up", "面试追问生成", 1, "AI 生成面试追问"),
    ("exercise_code_eval", "习题代码评测", 5, "习题代码 AI 评测"),
    ("ai_generate_cases", "AI 生成测试用例", 50, "从 Swagger 自动生成测试用例（每批次）"),
    ("bench_ai_analysis", "性能 AI 分析", 15, "性能测试结果 AI 分析"),
    ("report_ai_suggestions", "报告优化建议", 3, "测试报告 AI 优化建议"),
    ("jmeter_ai_assertions", "JMeter AI 断言", 2, "JMeter 脚本 AI 断言生成"),
]


def migrate():
    print(f"数据库路径: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # ── 1. 创建 ai_points_config 表 ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_points_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature VARCHAR(50) NOT NULL UNIQUE,
            display_name VARCHAR(100) NOT NULL,
            points_cost INTEGER NOT NULL DEFAULT 1,
            description VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ ai_points_config 表就绪")

    # ── 2. 创建 points_transactions 表 ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS points_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            tx_type VARCHAR(30) NOT NULL,
            source VARCHAR(100),
            related_feature VARCHAR(50),
            note VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 索引
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ptx_user_type ON points_transactions(user_id, tx_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ptx_created ON points_transactions(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ptx_user_id ON points_transactions(user_id)")
    print("  ✓ points_transactions 表就绪")

    # ── 3. 创建 ai_usage_logs 表 ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            feature VARCHAR(50) NOT NULL,
            points_cost INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_user_feature ON ai_usage_logs(user_id, feature)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_created ON ai_usage_logs(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_user_id ON ai_usage_logs(user_id)")
    print("  ✓ ai_usage_logs 表就绪")

    # ── 4. 写入默认积分配置 ──
    inserted = 0
    for feature, display_name, cost, desc in SEED_CONFIGS:
        try:
            cur.execute(
                "INSERT OR IGNORE INTO ai_points_config (feature, display_name, points_cost, description) VALUES (?, ?, ?, ?)",
                (feature, display_name, cost, desc),
            )
            if cur.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"  警告: 插入 {feature} 失败: {e}")

    conn.commit()
    conn.close()

    print(f"\n迁移完成!")
    print(f"  新建表: 3 张")
    print(f"  新增配置: {inserted} 条 (已存在则跳过)")


if __name__ == "__main__":
    migrate()
