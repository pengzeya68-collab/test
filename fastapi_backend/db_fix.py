
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "testmaster.db"

def fix_database():
    print(f"[DB Fix] Database path: {DB_PATH}")
    print(f"[DB Fix] Exists: {DB_PATH.exists()}")

    if not DB_PATH.exists():
        print("[DB Fix] Database does not exist yet.")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Check current table structure
        cursor.execute("PRAGMA table_info(api_cases)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"[DB Fix] Current columns in api_cases: {columns}")

        if "extractors" not in columns:
            print("[DB Fix] Adding 'extractors' column...")
            cursor.execute("ALTER TABLE api_cases ADD COLUMN extractors TEXT")
            conn.commit()
            print("[DB Fix] ✅ extractors column added!")
        else:
            print("[DB Fix] ✅ extractors column already exists!")

        # Verify the fix
        cursor.execute("PRAGMA table_info(api_cases)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"[DB Fix] Final columns: {final_columns}")

        return True
    except Exception as e:
        print(f"[DB Fix] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    fix_database()
