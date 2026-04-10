import sqlite3

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db')
cursor = conn.cursor()

# 检查所有可能有断言字段的表
tables_to_check = ['interface_test_cases', 'auto_test_cases', 'auto_test_plans', 'auto_test_report_results']

for table in tables_to_check:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    print(f"\n{table}: {col_names}")

    # 如果有 assert 或 rule 相关字段，显示数据
    for col in col_names:
        if 'assert' in col.lower() or 'rule' in col.lower() or 'expect' in col.lower():
            cursor.execute(f"SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 3")
            rows = cursor.fetchall()
            if rows:
                print(f"  {col} samples: {rows}")

conn.close()