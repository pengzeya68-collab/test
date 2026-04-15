#!/usr/bin/env python
"""Fix auto_test.db database - add body_type and content_type columns"""
import sqlite3
from pathlib import Path

INSTANCE_DIR = Path(__file__).resolve().parent / "instance"
DB_PATH = INSTANCE_DIR / "auto_test.db"

def fix_body_columns():
    """Check and add body_type and content_type columns to api_cases table"""
    if not DB_PATH.exists():
        print(f"[ERROR] Database file not found: {DB_PATH}")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current api_cases table columns: {columns}")

    # Add body_type column if missing
    if "body_type" not in columns:
        print("[INFO] Adding body_type column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN body_type TEXT DEFAULT 'none'")
            conn.commit()
            print("[OK] body_type column added!")
        except Exception as e:
            print(f"[ERROR] Failed to add body_type column: {e}")
            conn.close()
            return False
    else:
        print("[INFO] body_type column already exists")

    # Add content_type column if missing
    if "content_type" not in columns:
        print("[INFO] Adding content_type column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN content_type TEXT DEFAULT 'application/json'")
            conn.commit()
            print("[OK] content_type column added!")
        except Exception as e:
            print(f"[ERROR] Failed to add content_type column: {e}")
            conn.close()
            return False
    else:
        print("[INFO] content_type column already exists")

    # Also ensure params column exists
    if "params" not in columns:
        print("[INFO] Adding params column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN params TEXT")
            conn.commit()
            print("[OK] params column added!")
        except Exception as e:
            print(f"[ERROR] Failed to add params column: {e}")
            conn.close()
            return False
    else:
        print("[INFO] params column already exists")

    conn.close()
    print("[SUCCESS] Database fix complete!")
    return True

if __name__ == "__main__":
    fix_body_columns()