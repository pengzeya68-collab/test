import sqlite3

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db')
cursor = conn.cursor()

# 检查 plan_id=11 的报告
cursor.execute('SELECT id, plan_id, total_count, executed_at FROM interface_test_reports WHERE plan_id = 11 ORDER BY id DESC')
print('Reports for plan_id=11:')
for row in cursor.fetchall():
    print(f'  id={row[0]}, plan_id={row[1]}, total_count={row[2]}, executed_at={row[3]}')

# 找到报告11的最早的"最新"执行时间（因为有2个步骤，需要保留同一时间窗口内的）
cursor.execute('SELECT MIN(executed_at) FROM interface_test_report_results WHERE report_id = 11 AND id >= 867')
min_keep_date = cursor.fetchone()[0]
print(f'\nEarliest keep date: {min_keep_date}')

# 删除报告11的旧步骤（保留 867 和 868）
cursor.execute('DELETE FROM interface_test_report_results WHERE report_id = 11 AND id < 867')
deleted = cursor.rowcount
print(f'Deleted {deleted} orphan steps from report 11')

conn.commit()

# 验证
cursor.execute('SELECT COUNT(*) FROM interface_test_report_results WHERE report_id = 11')
print(f'Remaining steps for report 11: {cursor.fetchone()[0]}')

# 列出剩余步骤
cursor.execute('SELECT id, case_name FROM interface_test_report_results WHERE report_id = 11 ORDER BY id')
print('Remaining steps:')
for row in cursor.fetchall():
    print(f'  id={row[0]}, case_name={row[1]}')

conn.close()
print('\nCleanup done!')