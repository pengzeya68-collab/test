import sqlite3
conn = sqlite3.connect('instance/testmaster.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, base_url FROM interface_test_environments')
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]}, base_url: {row[2]}")
conn.close()