#!/usr/bin/env python3
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'testmaster.db')

print(f"Opening database: {db_path}")

if not os.path.exists(db_path):
    print(f"ERROR: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current status
cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", ('admin',))
row = cursor.fetchone()

if not row:
    print("ERROR: admin user not found!")
    print("Existing users:")
    cursor.execute("SELECT id, username, is_admin FROM users")
    for r in cursor.fetchall():
        print(f"  id={r[0]}, username={r[1]}, is_admin={r[2]}")
    conn.close()
    exit(1)

print(f"Current: id={row[0]}, username={row[1]}, is_admin={row[2]}")

# Update
cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
conn.commit()

# Check again
cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", ('admin',))
row = cursor.fetchone()
print(f"Updated: id={row[0]}, username={row[1]}, is_admin={row[2]}")

conn.close()
print("\n✅ SUCCESS: admin user is_admin = 1 (True)!")
print("Please clear browser localStorage and re-login, you can enter admin now!")
