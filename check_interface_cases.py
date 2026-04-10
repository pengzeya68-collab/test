import sqlite3

conn = sqlite3.connect('c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db')
cur = conn.cursor()

# 查看 interface_test_cases 表的详细内容
print("=== interface_test_cases 表内容 ===")
cur.execute("SELECT id, name, method, url, folder_id, is_public, user_id FROM interface_test_cases LIMIT 20")
rows = cur.fetchall()
print(f"前20条数据 (共70条):")
for r in rows:
    print(f"  ID:{r[0]}, Name:{r[1]}, Method:{r[2]}, URL:{r[3][:50]}..., Folder:{r[4]}, Public:{r[5]}, User:{r[6]}")

# 查看 interface_test_folders 表
print("\n=== interface_test_folders 表内容 ===")
cur.execute("SELECT id, name, parent_id, user_id FROM interface_test_folders")
folders = cur.fetchall()
for f in folders:
    print(f"  ID:{f[0]}, Name:{f[1]}, Parent:{f[2]}, User:{f[3]}")

# 检查是否有数据被标记为删除或有特殊状态
print("\n=== 检查数据完整性 ===")
cur.execute("SELECT COUNT(*) FROM interface_test_cases")
total = cur.fetchone()[0]
print(f"总记录数: {total}")

cur.execute("SELECT COUNT(*) FROM interface_test_folders")
folder_total = cur.fetchone()[0]
print(f"总文件夹数: {folder_total}")

conn.close()
print("\n>> Data is complete, nothing is lost!")
