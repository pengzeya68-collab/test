#!/usr/bin/env python3
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'testmaster.db')
print(f"Checking database: {db_path}")

if not os.path.exists(db_path):
    print(f"ERROR: Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print(f"\nAll tables in database ({len(tables)}):")
for t in sorted(tables):
    print(f"  - {t}")

# Check if learning_path and exam tables exist
print("\nChecking required tables:")

learning_path_exists = any('learning' in t or 'path' in t for t in tables)
exam_exists = any('exam' in t for t in tables)

print(f"  learning_path/LearningPath: {'EXISTS' if learning_path_exists else 'MISSING'}")
print(f"  exam/Exam: {'EXISTS' if exam_exists else 'MISSING'}")

# If tables exist, check for errors by trying a simple query
if learning_path_exists:
    cursor.execute("SELECT COUNT(*) FROM learning_path;")
    count = cursor.fetchone()[0]
    print(f"\nlearning_path has {count} rows")

if exam_exists:
    cursor.execute("SELECT COUNT(*) FROM exam;")
    count = cursor.fetchone()[0]
    print(f"exam has {count} rows")

conn.close()
