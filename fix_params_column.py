#!/usr/bin/env python
"""Direct fix for auto_test.db database, add params column"""
import sqlite3
from pathlib import Path

INSTANCE_DIR = Path(__file__).resolve().parent / "instance"
DB_PATH = INSTANCE_DIR / "auto_test.db"

def fix_params_column():
    """Check and add params column to api_cases table"""
    if not DB_PATH.exists():
        print(f"[ERROR] Database file not found: {DB_PATH}")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_cases'")
    if not cursor.fetchone():
        print("[ERROR] api_cases table does not exist")
        conn.close()
        return False

    # Check existing columns
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current api_cases table columns: {columns}")

    if "params" not in columns:
        print("[INFO] Adding params column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN params TEXT")
            conn.commit()
            print("[SUCCESS] params column added!")
        except Exception as e:
            print(f"[ERROR] Failed to add params column: {e}")
            conn.close()
            return False
    else:
        print("[INFO] params column already exists")

    # Also check extractors column
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [row[1] for row in cursor.fetchall()]
    if "extractors" not in columns:
        print("[INFO] Adding extractors column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN extractors TEXT")
            conn.commit()
            print("[SUCCESS] extractors column added!")
        except Exception as e:
            print(f"[ERROR] Failed to add extractors column: {e}")
            conn.close()
            return False
    else:
        print("[INFO] extractors column already exists")

    conn.close()
    print("[SUCCESS] Database fix complete!")
    return True

if __name__ == "__main__":
    fix_params_column()