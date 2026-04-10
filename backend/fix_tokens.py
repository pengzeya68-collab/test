#!/usr/bin/env python3
"""
数据修复脚本：为所有没有 webhook_token 的现有场景生成 UUID Token
用于 CI/CD Webhook 功能
"""

import uuid
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app import create_app
from backend.extensions import db
from backend.models.models import AutoTestPlan

app = create_app()

def fix_all_missing_tokens():
    with app.app_context():
        # 查询所有 webhook_token 为空的记录
        scenarios = AutoTestPlan.query.filter(
            (AutoTestPlan.webhook_token == None) |
            (AutoTestPlan.webhook_token == '')
        ).all()

        if not scenarios:
            print("[OK] 没有需要修复的记录，所有场景都已有 webhook_token")
            return 0

        print(f"[Info] 发现 {len(scenarios)} 条记录缺少 webhook_token，开始修复...")

        count = 0
        for scenario in scenarios:
            token = str(uuid.uuid4())
            scenario.webhook_token = token
            print(f"  - 场景 ID {scenario.id}: '{scenario.name}' → {token}")
            count += 1

        db.session.commit()
        print(f"\n[✅ 完成] 成功修复 {count} 条记录，所有场景现在都有了 webhook_token")
        return count

if __name__ == '__main__':
    fixed = fix_all_missing_tokens()
    sys.exit(0 if fixed >= 0 else 1)
