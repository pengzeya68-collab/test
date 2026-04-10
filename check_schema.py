#!/usr/bin/env python3
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'testmaster.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== learning_paths table schema ===")
cursor.execute("PRAGMA table_info(learning_paths);")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\n=== exams table schema ===")
cursor.execute("PRAGMA table_info(exams);")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

conn.close()
