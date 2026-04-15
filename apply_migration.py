
import sqlite3
import os

DB_FILE = r"c:\Users\lenovo\Desktop\TestMasterProject\fastapi_backend\testmaster.db"

print(f"Checking database at: {DB_FILE}")

if os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Current columns in api_cases: {columns}")
    
    if "extractors" not in columns:
        print("Adding extractors column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN extractors TEXT")
            conn.commit()
            print("✅ Success: extractors column added")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("✅ extractors column already exists")
    
    if "params" not in columns:
        print("Adding params column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN params TEXT")
            conn.commit()
            print("✅ Success: params column added")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("✅ params column already exists")
        
    # Verify
    cursor.execute("PRAGMA table_info(api_cases)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"Final columns: {final_columns}")
    
    conn.close()
else:
    print(f"Database file not found: {DB_FILE}")

print("\nDone.")

