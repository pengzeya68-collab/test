#!/usr/bin/env python3
"""
修复数据库中环境配置的 base_url，更新为正确的端口匹配你的服务
你的服务：
- Flask 后端: http://localhost:5000
- FastAPI 后端: http://localhost:5002
- 前端: http://localhost:5173
"""
import sqlite3
import os

# SQLite 数据库路径
db_path = 'instance/testmaster.db'

def main():
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        print("请检查路径是否正确")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询当前所有环境
    print("=" * 60)
    print("当前所有环境配置:")
    print("=" * 60)
    cursor.execute("SELECT id, name, base_url, user_id FROM interface_test_environments")
    envs = cursor.fetchall()
    for env in envs:
        print(f"  ID: {env[0]} | 名称: {env[1]} | base_url: {env[2]} | 用户ID: {env[3]}")

    print("\n" + "=" * 60)
    print("正在修复：将端口 3000 -> 5000， 5001 -> 5000 (Flask后端)")
    print("=" * 60)

    # 统计修改数量
    cursor.execute("SELECT COUNT(*) FROM interface_test_environments WHERE base_url LIKE '%:3000%' OR base_url LIKE '%:5001%'")
    count_before = cursor.fetchone()[0]
    print(f"需要修改 {count_before} 条环境配置")

    # 更新所有环境配置的 base_url 端口
    cursor.execute("""
        UPDATE interface_test_environments
        SET base_url = REPLACE(base_url, ':3000', ':5000')
    """)
    updated_3000 = cursor.rowcount
    cursor.execute("""
        UPDATE interface_test_environments
        SET base_url = REPLACE(base_url, ':5001', ':5000')
    """)
    updated_5001 = cursor.rowcount
    conn.commit()

    print(f"完成：修改了 {updated_3000 + updated_5001} 处端口")

    # 查看更新后
    print("\n" + "=" * 60)
    print("更新后的环境配置:")
    print("=" * 60)
    cursor.execute("SELECT id, name, base_url, user_id FROM interface_test_environments")
    envs = cursor.fetchall()
    for env in envs:
        print(f"  ID: {env[0]} | 名称: {env[1]} | base_url: {env[2]} | 用户ID: {env[3]}")

    # 检查是否有测试用例 URL 硬编码了错误端口
    print("\n" + "=" * 60)
    print("检查测试用例中硬编码的错误端口:")
    print("=" * 60)
    cursor.execute("""
        SELECT id, url FROM interface_test_cases
        WHERE url LIKE '%:3000%' OR url LIKE '%:5001%'
    """)
    bad_cases = cursor.fetchall()
    if bad_cases:
        print(f"发现 {len(bad_cases)} 个测试用例 URL 包含错误端口:")
        for case in bad_cases:
            print(f"  ID: {case[0]} | URL: {case[1]}")

        # 询问用户是否修复
        print("\n如果你想自动修复这些硬编码的URL，请在浏览器界面打开测试用例编辑，")
        print("或者我可以帮你批量替换端口 3000 -> 5000，5001 -> 5000。")
    else:
        print("✓ 没有发现硬编码错误端口的测试用例")

    conn.close()
    print("\n✓ 数据库修复完成！请重启后端服务再试。")

if __name__ == '__main__':
    main()
