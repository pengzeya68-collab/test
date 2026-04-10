# -*- coding: utf-8 -*-
"""
批量数据库清洗脚本
战役二：清洗数据库里的垃圾硬编码 URL

功能：
1. 将所有包含 localhost:3000 / localhost:5000 / 127.0.0.1 的硬编码 URL
   替换为标准格式 {{base_url}}{{api_prefix}}/path
2. 统计受影响的行数
"""

import sys
import os
import re

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app import create_app
from backend.extensions import db
from backend.models.models import AutoTestCase

app = create_app()

def clean_hardcoded_urls():
    with app.app_context():
        # 查询所有用例
        cases = AutoTestCase.query.all()
        modified_count = 0
        skipped_count = 0

        print(f"总共查询到 {len(cases)} 个接口用例\n")

        # 硬编码 localhost 模式
        patterns = [
            re.compile(r'https?://localhost:?\d*'),
            re.compile(r'https?://127\.0\.0\.1:?\d*'),
        ]

        for case in cases:
            if not case.url:
                skipped_count += 1
                continue

            original_url = case.url
            new_url = original_url

            # 替换所有匹配的硬编码
            for pattern in patterns:
                new_url = pattern.sub('{{base_url}}', new_url)

            # 如果修改了，打印并保存
            if new_url != original_url:
                print(f"✓ 修改 ID={case.id}: {original_url} → {new_url}")
                case.url = new_url
                modified_count += 1

        # 提交修改
        if modified_count > 0:
            db.session.commit()
            print(f"\n✅ 批量修改完成！共修改 {modified_count} 个 URL，跳过 {skipped_count} 个")
        else:
            print(f"\n✓ 没有找到需要修改的硬编码 URL，跳过 {skipped_count} 个")

        # 检查是否还有空 body 的 POST/PUT 请求
        print("\n🔍 检查 POST/PUT 请求是否有空 body...")
        empty_body_count = 0
        post_put_cases = AutoTestCase.query.filter(AutoTestCase.method.in_(['POST', 'PUT'])).all()

        for case in post_put_cases:
            if not case.body or case.body.strip() == '':
                # 添加默认空 JSON 对象
                case.body = '{}'
                empty_body_count += 1
                print(f"✓ 补齐 ID={case.id} method={case.method} 空 body → {{}}")

        if empty_body_count > 0:
            db.session.commit()
            print(f"\n✅ 补齐完成！共补齐 {empty_body_count} 个空 body")
        else:
            print("\n✓ 没有找到需要补齐的空 body")

        db.session.close()

if __name__ == '__main__':
    clean_hardcoded_urls()
